"""Cross-session memory service.

Generates and retrieves conversation summaries to maintain context
across chat sessions. Updates every N messages (configurable).
"""

from __future__ import annotations

import json
import logging
from datetime import UTC, datetime

from supabase import Client

logger = logging.getLogger(__name__)


class MemoryService:
    def __init__(self, supabase: Client, openrouter_api_key: str, model: str, update_interval: int = 5) -> None:
        self._client = supabase
        self._api_key = openrouter_api_key
        self._model = model
        self._update_interval = update_interval

    def get_summary(self, user_id: str) -> str | None:
        result = (
            self._client.table("user_memory")
            .select("summary_text")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if rows and rows[0].get("summary_text"):
            return rows[0]["summary_text"]
        return None

    def get_topics(self, user_id: str) -> list[str]:
        result = (
            self._client.table("user_memory")
            .select("topics")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if rows and rows[0].get("topics"):
            return rows[0]["topics"]
        return []

    def should_update(self, session_id: str) -> bool:
        result = (
            self._client.table("chat_messages")
            .select("id", count="exact")
            .eq("session_id", session_id)
            .execute()
        )
        count = result.count or 0
        return count > 0 and count % self._update_interval == 0

    def update_summary(self, user_id: str, session_id: str) -> None:
        messages = (
            self._client.table("chat_messages")
            .select("role,content")
            .eq("session_id", session_id)
            .order("created_at")
            .limit(50)
            .execute()
            .data
            or []
        )
        if not messages:
            return

        conversation_text = "\n".join(f"{m['role']}: {m['content']}" for m in messages)
        prompt = (
            "Summarize this conversation's key topics and user preferences "
            "in 2-3 sentences. Focus on what funds or topics the user asked about.\n\n"
            f"{conversation_text}"
        )

        try:
            import httpx

            resp = httpx.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": self._model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 200,
                },
                timeout=30.0,
            )
            resp.raise_for_status()
            data = resp.json()
            summary = data["choices"][0]["message"]["content"].strip()
        except Exception:
            logger.exception("memory_summary_generation_failed")
            return

        topics = self._extract_topics(summary)
        now_iso = datetime.now(UTC).isoformat()

        existing = (
            self._client.table("user_memory")
            .select("id,summary_text")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
            .data
            or []
        )

        if existing:
            old_summary = existing[0].get("summary_text") or ""
            merged = f"{old_summary}\n---\n{summary}" if old_summary else summary
            if len(merged) > 2000:
                merged = merged[-2000:]
            self._client.table("user_memory").update({
                "summary_text": merged,
                "topics": topics,
                "updated_at": now_iso,
            }).eq("user_id", user_id).execute()
        else:
            self._client.table("user_memory").insert({
                "user_id": user_id,
                "summary_text": summary,
                "topics": topics,
                "updated_at": now_iso,
            }).execute()

    def _extract_topics(self, summary: str) -> list[str]:
        keywords = [
            "exit load", "expense ratio", "NAV", "returns", "SIP",
            "tax", "ELSS", "large cap", "mid cap", "small cap",
            "flexi cap", "debt", "hybrid", "ETF",
        ]
        found = []
        lower = summary.lower()
        for kw in keywords:
            if kw.lower() in lower:
                found.append(kw)
        return found[:10]
