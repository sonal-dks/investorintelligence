"""ChatService — orchestrates the full RAG pipeline for Smart Search.

Flow per message:
  1. PII detection → redact
  2. Intent routing (factual/action/safety/clarification)
  3. Refusal check for advice
  4. RAG retrieval (from Phase 02 pipeline)
  5. Build prompt with system instruction + memory + context + history
  6. LLM call (primary → fallback)
  7. Store message pair
  8. Async memory update
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime
from threading import Thread

from supabase import Client

from ..models.schemas import ChatMessageResponse, Citation, IntentClassification
from .approval_workflow_service import ApprovalWorkflowService
from .intent_router import IntentRouter
from .llm_client import LLMClient
from .memory_service import MemoryService
from .pii_detector import PIIDetector
from .refusal_classifier import RefusalClassifier

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a knowledgeable mutual fund information assistant for the Investor Ops Intelligence Suite. Your role is to provide accurate, factual information about mutual funds based ONLY on the provided context.

RULES:
1. Answer ONLY based on the provided context. If information is not in the context, say "I don't have specific information about that."
2. NEVER provide investment advice, predictions, or recommendations.
3. Include relevant citations when referencing fund data.
4. Keep answers concise and well-structured.
5. Use bullet points for multiple data points.
6. Always mention the source fund name when citing data.
7. If the user asks about a fund not in your context, say so clearly.

CONTEXT FROM KNOWLEDGE BASE:
{context}

USER MEMORY (previous conversations):
{memory}"""

ACTION_RESPONSE_TEMPLATE = (
    "I understand you'd like to {action_desc}. I can help facilitate that. "
    "Would you like me to proceed with setting this up? "
    "An admin will review and approve the action before it's executed."
)

SAFETY_RESPONSE = (
    "I'm designed to help with mutual fund information queries. "
    "I cannot modify my instructions or behavior. "
    "How can I help you with mutual fund information today?"
)

RAG_GUARDRAIL_REFUSAL = (
    "I do not have enough verified context from the knowledge base to answer that safely. "
    "Please ask about a specific fund, fee, return metric, or booking workflow present in the platform data."
)


class ChatService:
    def __init__(
        self,
        supabase: Client,
        llm: LLMClient,
        memory: MemoryService,
        retrieval_fn,
        pii: PIIDetector | None = None,
        refusal: RefusalClassifier | None = None,
        intent_router: IntentRouter | None = None,
        approval_workflow: ApprovalWorkflowService | None = None,
        max_history: int = 10,
    ) -> None:
        self._client = supabase
        self._llm = llm
        self._memory = memory
        self._retrieval_fn = retrieval_fn
        self._pii = pii or PIIDetector()
        self._refusal = refusal or RefusalClassifier()
        self._intent_router = intent_router or IntentRouter()
        self._approval_workflow = approval_workflow or ApprovalWorkflowService(supabase)
        self._max_history = max_history

    def _retrieve(self, query: str, corpus_filter: str | None = None):
        """Compatibility shim: retrieval_fn may or may not accept corpus_filter."""
        try:
            return self._retrieval_fn(query, corpus_filter=corpus_filter)
        except TypeError:
            return self._retrieval_fn(query)

    def process_message(
        self,
        session_id: str,
        user_id: str,
        content: str,
    ) -> ChatMessageResponse:
        started = time.time()
        message_id = str(uuid.uuid4())
        now_iso = datetime.now(UTC).isoformat()

        cleaned_text, pii_findings = self._pii.scan(content)
        pii_detected = len(pii_findings) > 0

        intent = self._intent_router.classify(cleaned_text)

        if intent.intent_type == "safety":
            return self._build_response(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                user_content=content,
                assistant_content=SAFETY_RESPONSE,
                citations=[],
                metadata={
                    "pii_detected": pii_detected,
                    "model_used": "none",
                    "intent_type": intent.intent_type,
                    "intent_confidence": intent.confidence,
                    "refusal_triggered": True,
                    "response_time_ms": int((time.time() - started) * 1000),
                },
                now_iso=now_iso,
            )

        should_refuse, refusal_reason = self._refusal.check(cleaned_text)
        if should_refuse and refusal_reason:
            return self._build_response(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                user_content=content,
                assistant_content=refusal_reason,
                citations=[],
                metadata={
                    "pii_detected": pii_detected,
                    "model_used": "none",
                    "intent_type": intent.intent_type,
                    "intent_confidence": intent.confidence,
                    "refusal_triggered": True,
                    "response_time_ms": int((time.time() - started) * 1000),
                },
                now_iso=now_iso,
            )

        if intent.intent_type == "action":
            action_desc = self._extract_action_description(cleaned_text)
            approval_result = self._create_or_update_approval(
                session_id=session_id,
                user_id=user_id,
                content=content,
            )
            assistant_content = ACTION_RESPONSE_TEMPLATE.format(action_desc=action_desc)
            return self._build_response(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                user_content=content,
                assistant_content=assistant_content,
                citations=[],
                metadata={
                    "pii_detected": pii_detected,
                    "model_used": "none",
                    "intent_type": intent.intent_type,
                    "intent_confidence": intent.confidence,
                    "refusal_triggered": False,
                    "approval_workflow": approval_result,
                    "response_time_ms": int((time.time() - started) * 1000),
                },
                now_iso=now_iso,
            )

        retrieval_result = None
        corpus_meta: dict[str, object] = {}
        if intent.intent_type == "factual":
            classify_factual = getattr(self._intent_router, "classify_factual_corpus", None)
            corp_hint = (
                classify_factual(cleaned_text)
                if callable(classify_factual)
                else None
            )
            retrieval_corpus = getattr(corp_hint, "retrieval_corpus", None) if corp_hint is not None else None
            corpus_confidence_raw = getattr(corp_hint, "confidence", 0.0) if corp_hint is not None else 0.0
            try:
                corpus_confidence = float(corpus_confidence_raw)
            except (TypeError, ValueError):
                corpus_confidence = 0.0
            corpus_reasoning = getattr(corp_hint, "reasoning_tag", "corpus_classifier_unavailable")
            corpus_meta = {
                "factual_corpus": retrieval_corpus,
                "factual_corpus_confidence": corpus_confidence,
                "factual_corpus_reasoning": corpus_reasoning,
            }
            if retrieval_corpus and corpus_confidence >= 0.7:
                retrieval_result = self._retrieve(
                    cleaned_text, corpus_filter=retrieval_corpus
                )
                if retrieval_result is not None and len(retrieval_result.results) == 0:
                    retrieval_result = self._retrieve(cleaned_text, corpus_filter=None)
                    corpus_meta["factual_corpus_fallback"] = "empty_filtered_results"
            else:
                retrieval_result = self._retrieve(cleaned_text, corpus_filter=None)
        else:
            retrieval_result = self._retrieve(cleaned_text, corpus_filter=None)

        context_chunks = retrieval_result.results if retrieval_result else []
        if len(context_chunks) == 0:
            return self._build_response(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                user_content=content,
                assistant_content=RAG_GUARDRAIL_REFUSAL,
                citations=[],
                metadata={
                    "pii_detected": pii_detected,
                    "model_used": "none",
                    "intent_type": intent.intent_type,
                    "intent_confidence": intent.confidence,
                    "refusal_triggered": True,
                    "guardrail_reason": "no_retrieval_context",
                    **corpus_meta,
                    "response_time_ms": int((time.time() - started) * 1000),
                },
                now_iso=now_iso,
            )

        context_text = "\n\n".join(
            f"[{i+1}] {chunk.text}" for i, chunk in enumerate(context_chunks)
        )
        if not context_text:
            context_text = "No relevant information found in the knowledge base."

        memory_summary = self._memory.get_summary(user_id) or "No previous conversation context."

        system_message = SYSTEM_PROMPT.format(context=context_text, memory=memory_summary)

        history = self._get_conversation_history(session_id)
        messages = [
            {"role": "system", "content": system_message},
            *history,
            {"role": "user", "content": cleaned_text},
        ]

        llm_response = self._llm.generate(messages)
        assistant_text = llm_response.text
        model_used = llm_response.model
        judge_result = self._judge_grounding(cleaned_text, context_text, assistant_text)
        if judge_result != "PASS":
            assistant_text = RAG_GUARDRAIL_REFUSAL

        if context_chunks and retrieval_result and retrieval_result.resolved_fund_slug:
            assistant_text = assistant_text.rstrip()
            if not assistant_text.endswith("This is not investment advice."):
                assistant_text += "\n\n_This is not investment advice._"

        citations = self._extract_citations(context_chunks, assistant_text)

        response_time_ms = int((time.time() - started) * 1000)

        logger.info(
            "llm_request_usage",
            extra={
                "session_id": session_id,
                "user_id": user_id,
                "model": model_used,
                "intent": intent.intent_type,
                "prompt_tokens": llm_response.prompt_tokens,
                "completion_tokens": llm_response.completion_tokens,
                "total_tokens": llm_response.total_tokens,
                "cost_usd": llm_response.cost_usd,
                "retrieval_count": len(context_chunks),
                "response_time_ms": response_time_ms,
            },
        )

        response = self._build_response(
            message_id=message_id,
            session_id=session_id,
            user_id=user_id,
            user_content=content,
            assistant_content=assistant_text,
            citations=citations,
            metadata={
                "pii_detected": pii_detected,
                "model_used": model_used,
                "intent_type": intent.intent_type,
                "intent_confidence": intent.confidence,
                "refusal_triggered": False,
                **corpus_meta,
                "retrieval_count": len(context_chunks),
                "retrieval_time_ms": retrieval_result.query_time_ms if retrieval_result else 0,
                "resolved_fund": retrieval_result.resolved_fund_slug if retrieval_result else None,
                "response_time_ms": response_time_ms,
                "prompt_tokens": llm_response.prompt_tokens,
                "completion_tokens": llm_response.completion_tokens,
                "total_tokens": llm_response.total_tokens,
                "cost_usd": llm_response.cost_usd,
                "judge_result": judge_result,
            },
            now_iso=now_iso,
        )

        if self._memory.should_update(session_id):
            thread = Thread(
                target=self._memory.update_summary,
                args=(user_id, session_id),
                daemon=True,
            )
            thread.start()

        return response

    def _judge_grounding(self, user_query: str, context_text: str, assistant_text: str) -> str:
        judge_prompt = (
            "You are a strict RAG safety judge.\n"
            "Return only PASS or FAIL.\n"
            "PASS only if the assistant answer is fully supported by the provided context. "
            "If it adds facts not present in context, return FAIL.\n\n"
            f"USER_QUERY:\n{user_query}\n\n"
            f"CONTEXT:\n{context_text}\n\n"
            f"ASSISTANT_ANSWER:\n{assistant_text}\n"
        )
        try:
            judge = self._llm.generate(
                [
                    {"role": "system", "content": "You output only PASS or FAIL."},
                    {"role": "user", "content": judge_prompt},
                ],
                max_tokens=5,
            )
            out = (judge.text or "").strip().upper()
            return "PASS" if out.startswith("PASS") else "FAIL"
        except Exception:
            logger.exception("judge_check_failed")
            return "FAIL"

    def _build_response(
        self,
        message_id: str,
        session_id: str,
        user_id: str,
        user_content: str,
        assistant_content: str,
        citations: list[Citation],
        metadata: dict,
        now_iso: str,
    ) -> ChatMessageResponse:
        self._store_message(session_id, "user", user_content, now_iso)
        self._store_message(
            session_id,
            "assistant",
            assistant_content,
            now_iso,
            citations=[c.model_dump() for c in citations],
            metadata=metadata,
        )
        self._update_session_title(session_id, user_content)
        self._log_activity(user_id, session_id)

        return ChatMessageResponse(
            id=message_id,
            role="assistant",
            content=assistant_content,
            citations=citations,
            metadata=metadata,
            created_at=now_iso,
        )

    def _store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        created_at: str,
        citations: list | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            self._client.table("chat_messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content,
                "citations": citations or [],
                "metadata": metadata or {},
                "created_at": created_at,
            }).execute()
        except Exception:
            logger.exception("store_message_failed")

    def _update_session_title(self, session_id: str, first_message: str) -> None:
        try:
            result = (
                self._client.table("chat_messages")
                .select("id", count="exact")
                .eq("session_id", session_id)
                .execute()
            )
            if (result.count or 0) <= 2:
                title = first_message[:60].strip()
                if len(first_message) > 60:
                    title += "..."
                self._client.table("chat_sessions").update({
                    "title": title,
                    "last_message_at": datetime.now(UTC).isoformat(),
                }).eq("id", session_id).execute()
            else:
                self._client.table("chat_sessions").update({
                    "last_message_at": datetime.now(UTC).isoformat(),
                }).eq("id", session_id).execute()
        except Exception:
            logger.exception("update_session_title_failed")

    def _log_activity(self, user_id: str, session_id: str) -> None:
        try:
            existing = (
                self._client.table("activity_log")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("event_type", "chatbot_used")
                .eq("metadata->>session_id", session_id)
                .execute()
            )
            if (existing.count or 0) == 0:
                self._client.table("activity_log").insert({
                    "user_id": user_id,
                    "event_type": "chatbot_used",
                    "metadata": {"session_id": session_id},
                }).execute()
        except Exception:
            logger.exception("log_activity_failed")

    def _get_conversation_history(self, session_id: str) -> list[dict[str, str]]:
        try:
            rows = (
                self._client.table("chat_messages")
                .select("role,content")
                .eq("session_id", session_id)
                .order("created_at")
                .limit(self._max_history * 2)
                .execute()
                .data
                or []
            )
            return [{"role": r["role"], "content": r["content"]} for r in rows if r["role"] in ("user", "assistant")]
        except Exception:
            logger.exception("get_history_failed")
            return []

    def _extract_citations(self, chunks, assistant_text: str) -> list[Citation]:
        citations = []
        seen_urls = set()
        for chunk in chunks:
            source_url = getattr(chunk.metadata, "source_url", "") or ""
            fund_slug = getattr(chunk.metadata, "fund_slug", "") or ""
            corpus = getattr(chunk.metadata, "corpus", "mutual_fund") or "mutual_fund"

            if not source_url:
                if corpus == "fee_explainer":
                    source_url = "https://groww.in"
                else:
                    source_url = f"https://groww.in/mutual-funds/{fund_slug}" if fund_slug else ""

            if source_url in seen_urls:
                continue

            snippet = chunk.text[:100]
            if any(part.lower() in assistant_text.lower() for part in snippet.split()[:5] if len(part) > 3):
                if corpus == "fee_explainer" or fund_slug == "__fee_explainer__":
                    fund_name = "Fee explainer"
                else:
                    fund_name = (
                        " ".join(part.capitalize() for part in fund_slug.replace("-", " ").split())
                        if fund_slug
                        else "Unknown Fund"
                    )
                citations.append(Citation(
                    text=snippet,
                    source_url=source_url,
                    fund=fund_name,
                ))
                seen_urls.add(source_url)

        return citations[:5]

    def _extract_action_description(self, text: str) -> str:
        lower = text.lower()
        if "book" in lower or "schedule" in lower or "call" in lower:
            return "schedule a call with an advisor"
        if "email" in lower:
            return "draft an email"
        if "cancel" in lower:
            return "cancel a booking"
        if "reschedule" in lower:
            return "reschedule a booking"
        return "take an action"

    def _create_or_update_approval(self, session_id: str, user_id: str, content: str) -> dict:
        try:
            profile = (
                self._client.table("profiles")
                .select("full_name")
                .eq("id", user_id)
                .limit(1)
                .execute()
                .data
                or []
            )
            investor_name = profile[0].get("full_name", "Investor") if profile else "Investor"
            return self._approval_workflow.process_action_intent(
                session_id=session_id,
                user_id=user_id,
                investor_name=investor_name,
                content=content,
                source_type="chat",
            )
        except Exception:
            logger.exception("approval_workflow_failed")
            return {"created": False, "error": "approval_workflow_failed"}
