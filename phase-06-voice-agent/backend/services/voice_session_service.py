"""VoiceSessionService — session + message CRUD for the voice agent.

Mirrors ChatService from Phase 05 but stores in voice_sessions / voice_messages
and adds the `input_mode` field to messages.
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import UTC, datetime

from supabase import Client

from ..models.schemas import Citation, VoiceMessageResponse

logger = logging.getLogger(__name__)

VOICE_SYSTEM_PROMPT = """You are a knowledgeable mutual fund information assistant for the Investor Ops Intelligence Suite. Your role is to provide accurate, factual information about mutual funds based ONLY on the provided context.

RULES:
1. Answer ONLY based on the provided context. If information is not in the context, say "I don't have specific information about that."
2. NEVER provide investment advice, predictions, or recommendations.
3. Include relevant citations when referencing fund data.
4. Keep responses CONCISE — maximum 3 sentences for voice mode.
5. Use simple language suitable for spoken delivery.
6. Always mention the source fund name when citing data.

CONTEXT FROM KNOWLEDGE BASE:
{context}

USER MEMORY (previous conversations):
{memory}"""


class VoiceSessionService:
    def __init__(
        self,
        supabase: Client,
        llm_client,
        memory_service,
        retrieval_fn,
        pii_detector,
        refusal_classifier,
        intent_router,
        approval_workflow=None,
        max_history: int = 10,
    ) -> None:
        self._client = supabase
        self._llm = llm_client
        self._memory = memory_service
        self._retrieval_fn = retrieval_fn
        self._pii = pii_detector
        self._refusal = refusal_classifier
        self._intent_router = intent_router
        self._approval_workflow = approval_workflow
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
        input_mode: str = "text",
    ) -> VoiceMessageResponse:
        started = time.time()
        message_id = str(uuid.uuid4())
        now_iso = datetime.now(UTC).isoformat()

        cleaned_text, pii_findings = self._pii.scan(content)
        pii_detected = len(pii_findings) > 0

        intent = self._intent_router.classify(cleaned_text)

        if intent.intent_type == "safety":
            safety_msg = (
                "I'm designed to help with mutual fund information queries. "
                "How can I help you with mutual fund information today?"
            )
            return self._build_response(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                user_content=content,
                assistant_content=safety_msg,
                input_mode=input_mode,
                citations=[],
                metadata={"pii_detected": pii_detected, "model_used": "none", "intent_type": "safety", "refusal_triggered": True},
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
                input_mode=input_mode,
                citations=[],
                metadata={"pii_detected": pii_detected, "model_used": "none", "intent_type": intent.intent_type, "refusal_triggered": True},
                now_iso=now_iso,
            )

        if intent.intent_type == "action":
            approval_result = self._create_or_update_approval(session_id=session_id, user_id=user_id, content=content)
            action_msg = (
                "I understand you'd like to take an action. "
                "An admin will review and approve before it's executed."
            )
            return self._build_response(
                message_id=message_id,
                session_id=session_id,
                user_id=user_id,
                user_content=content,
                assistant_content=action_msg,
                input_mode=input_mode,
                citations=[],
                metadata={"pii_detected": pii_detected, "model_used": "none", "intent_type": "action", "approval_workflow": approval_result},
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

        context_text = "\n\n".join(
            f"[{i + 1}] {chunk.text}" for i, chunk in enumerate(context_chunks)
        )
        if not context_text:
            context_text = "No relevant information found in the knowledge base."

        memory_summary = self._memory.get_summary(user_id) or "No previous conversation context."

        system_message = VOICE_SYSTEM_PROMPT.format(context=context_text, memory=memory_summary)

        history = self._get_conversation_history(session_id)
        messages = [
            {"role": "system", "content": system_message},
            *history,
            {"role": "user", "content": cleaned_text},
        ]

        llm_response = self._llm.generate(messages)
        assistant_text = llm_response.text
        model_used = llm_response.model

        citations = self._extract_citations(context_chunks, assistant_text)
        response_time_ms = int((time.time() - started) * 1000)

        logger.info(
            "voice_llm_request",
            extra={
                "session_id": session_id,
                "model": model_used,
                "input_mode": input_mode,
                "retrieval_count": len(context_chunks),
                "response_time_ms": response_time_ms,
            },
        )

        return self._build_response(
            message_id=message_id,
            session_id=session_id,
            user_id=user_id,
            user_content=content,
            assistant_content=assistant_text,
            input_mode=input_mode,
            citations=citations,
            metadata={
                "pii_detected": pii_detected,
                "model_used": model_used,
                "intent_type": intent.intent_type,
                **corpus_meta,
                "retrieval_count": len(context_chunks),
                "response_time_ms": response_time_ms,
                "input_mode": input_mode,
            },
            now_iso=now_iso,
        )

    def _build_response(
        self,
        message_id: str,
        session_id: str,
        user_id: str,
        user_content: str,
        assistant_content: str,
        input_mode: str,
        citations: list[Citation],
        metadata: dict,
        now_iso: str,
    ) -> VoiceMessageResponse:
        self._store_message(session_id, "user", user_content, input_mode, now_iso)
        self._store_message(
            session_id, "assistant", assistant_content, input_mode, now_iso,
            citations=[c.model_dump() for c in citations],
            metadata=metadata,
        )
        self._update_session_title(session_id, user_content)
        self._log_activity(user_id, session_id)

        return VoiceMessageResponse(
            id=message_id,
            role="assistant",
            content=assistant_content,
            citations=citations,
            metadata=metadata,
            voice_hint="concise" if input_mode == "voice" else "normal",
            created_at=now_iso,
        )

    def _store_message(
        self,
        session_id: str,
        role: str,
        content: str,
        input_mode: str,
        created_at: str,
        citations: list | None = None,
        metadata: dict | None = None,
    ) -> None:
        try:
            self._client.table("voice_messages").insert({
                "session_id": session_id,
                "role": role,
                "content": content,
                "input_mode": input_mode,
                "citations": citations or [],
                "metadata": metadata or {},
                "created_at": created_at,
            }).execute()
        except Exception:
            logger.exception("store_voice_message_failed")

    def _update_session_title(self, session_id: str, first_message: str) -> None:
        try:
            result = (
                self._client.table("voice_messages")
                .select("id", count="exact")
                .eq("session_id", session_id)
                .execute()
            )
            if (result.count or 0) <= 2:
                title = first_message[:60].strip()
                if len(first_message) > 60:
                    title += "..."
                self._client.table("voice_sessions").update({
                    "title": title,
                    "last_message_at": datetime.now(UTC).isoformat(),
                }).eq("id", session_id).execute()
            else:
                self._client.table("voice_sessions").update({
                    "last_message_at": datetime.now(UTC).isoformat(),
                }).eq("id", session_id).execute()
        except Exception:
            logger.exception("update_voice_session_title_failed")

    def _log_activity(self, user_id: str, session_id: str) -> None:
        try:
            existing = (
                self._client.table("activity_log")
                .select("id", count="exact")
                .eq("user_id", user_id)
                .eq("event_type", "voice_agent_used")
                .eq("metadata->>session_id", session_id)
                .execute()
            )
            if (existing.count or 0) == 0:
                self._client.table("activity_log").insert({
                    "user_id": user_id,
                    "event_type": "voice_agent_used",
                    "metadata": {"session_id": session_id},
                }).execute()
        except Exception:
            logger.exception("log_voice_activity_failed")

    def _get_conversation_history(self, session_id: str) -> list[dict[str, str]]:
        try:
            rows = (
                self._client.table("voice_messages")
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
            logger.exception("get_voice_history_failed")
            return []

    def _extract_citations(self, chunks, assistant_text: str) -> list[Citation]:
        citations: list[Citation] = []
        seen_urls: set[str] = set()
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
                citations.append(Citation(text=snippet, source_url=source_url, fund=fund_name))
                seen_urls.add(source_url)

        return citations[:5]

    def _create_or_update_approval(self, session_id: str, user_id: str, content: str) -> dict:
        if self._approval_workflow is None:
            return {"created": False, "error": "approval_workflow_unavailable"}
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
                source_type="voice",
            )
        except Exception:
            logger.exception("voice_approval_workflow_failed")
            return {"created": False, "error": "approval_workflow_failed"}
