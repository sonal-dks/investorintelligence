"""Phase 07 approval workflow integration for live chat/voice paths."""

from __future__ import annotations

import hashlib
import uuid
from datetime import UTC, datetime


class ApprovalWorkflowService:
    def __init__(self, supabase_client) -> None:
        self._client = supabase_client

    def process_action_intent(
        self,
        session_id: str,
        user_id: str,
        investor_name: str,
        content: str,
        source_type: str,
    ) -> dict:
        intent_type = self._detect_intent_type(content)
        confidence = self._confidence(content)
        intent_hash = self._intent_hash(session_id, intent_type, content)
        now_iso = datetime.now(UTC).isoformat()

        if confidence < 0.7:
            return {"created": False, "intent_type": intent_type, "confidence": confidence, "intent_hash": intent_hash}

        if intent_type == "cancel_booking":
            self._cancel_pending(session_id, user_id, now_iso)
            return {"created": False, "cancelled": True, "intent_type": intent_type, "confidence": confidence, "intent_hash": intent_hash}

        if intent_type == "reschedule":
            self._reschedule_pending(session_id, content, now_iso)
            return {"created": False, "modified": True, "intent_type": intent_type, "confidence": confidence, "intent_hash": intent_hash}

        existing = (
            self._client.table("approvals")
            .select("id")
            .eq("source_session_id", session_id)
            .eq("intent_hash", intent_hash)
            .eq("status", "pending")
            .limit(1)
            .execute()
            .data
            or []
        )
        if existing:
            return {"created": False, "duplicate": True, "intent_type": intent_type, "confidence": confidence, "intent_hash": intent_hash}

        action_type = "booking" if intent_type == "booking" else intent_type
        payload = {
            "topic": self._topic(content),
            "time_preference": self._time_preference(content),
            "source_message": content,
            "required_fields_ok": True,
        }
        row = {
            "id": str(uuid.uuid4()),
            "action_type": action_type,
            "title": f"{action_type.replace('_', ' ').title()} - {payload['topic'][:60]}",
            "description": "Generated from action intent",
            "investor_id": user_id,
            "investor_name": investor_name,
            "status": "pending",
            "priority": "medium",
            "payload": payload,
            "source_session_id": session_id,
            "source_type": source_type,
            "intent_hash": intent_hash,
            "created_at": now_iso,
        }
        self._client.table("approvals").insert(row).execute()
        return {"created": True, "intent_type": intent_type, "confidence": confidence, "intent_hash": intent_hash}

    def _cancel_pending(self, session_id: str, user_id: str, now_iso: str) -> None:
        rows = (
            self._client.table("approvals")
            .select("id")
            .eq("source_session_id", session_id)
            .eq("investor_id", user_id)
            .eq("status", "pending")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return
        self._client.table("approvals").update(
            {"status": "rejected", "reviewed_by": "system-intent", "reviewed_at": now_iso}
        ).eq("id", rows[0]["id"]).execute()

    def _reschedule_pending(self, session_id: str, content: str, now_iso: str) -> None:
        rows = (
            self._client.table("approvals")
            .select("id,payload")
            .eq("source_session_id", session_id)
            .eq("status", "pending")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return
        payload = rows[0].get("payload") or {}
        payload["time_preference"] = self._time_preference(content)
        payload["source_message"] = content
        self._client.table("approvals").update({"payload": payload, "reviewed_at": now_iso}).eq("id", rows[0]["id"]).execute()

    @staticmethod
    def _detect_intent_type(content: str) -> str:
        text = content.lower()
        if "cancel" in text or "never mind" in text:
            return "cancel_booking"
        if "reschedule" in text or "postpone" in text:
            return "reschedule"
        if "email" in text or "mail" in text:
            return "email"
        if "note" in text:
            return "note"
        if "follow up" in text or "follow-up" in text:
            return "follow_up"
        return "booking"

    @staticmethod
    def _confidence(content: str) -> float:
        return 0.55 if "maybe" in content.lower() else 0.88

    @staticmethod
    def _intent_hash(session_id: str, intent_type: str, content: str) -> str:
        digest = hashlib.sha256(f"{session_id}:{intent_type}:{content.lower().strip()}".encode("utf-8")).hexdigest()
        return digest[:16]

    @staticmethod
    def _topic(content: str) -> str:
        parts = content.split("about", 1)
        return parts[1].strip() if len(parts) > 1 else content[:80]

    @staticmethod
    def _time_preference(content: str) -> str:
        text = content.lower()
        if "next week" in text:
            return "next week"
        if "tomorrow" in text:
            return "tomorrow"
        return "unspecified"
