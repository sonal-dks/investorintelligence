from __future__ import annotations

from datetime import UTC, datetime

from backend.models.schemas import Approval


class ApprovalService:
    def __init__(self) -> None:
        self._items: dict[str, Approval] = {}

    def upsert_pending(self, approval: Approval) -> Approval:
        for item in self._items.values():
            if item.source_session_id == approval.source_session_id and item.intent_hash == approval.intent_hash and item.status == 'pending':
                return item
        self._items[approval.id] = approval
        return approval

    def list(self, status: str = 'all', user_id: str | None = None) -> list[Approval]:
        values = list(self._items.values())
        if status != 'all':
            values = [v for v in values if v.status == status]
        if user_id:
            values = [v for v in values if v.investor_id == user_id]
        return sorted(values, key=lambda x: x.created_at, reverse=True)

    def get(self, approval_id: str) -> Approval | None:
        return self._items.get(approval_id)

    def patch(self, approval_id: str, status: str, reviewed_by: str | None) -> Approval | None:
        item = self._items.get(approval_id)
        if item is None:
            return None
        reviewed_at = datetime.now(UTC).isoformat() if status in ('approved', 'rejected') else None
        updated = item.model_copy(update={
            'status': status,
            'reviewed_by': reviewed_by,
            'reviewed_at': reviewed_at,
        })
        self._items[approval_id] = updated
        return updated

    def cancel_by_intent_hash(self, session_id: str, intent_hash: str) -> None:
        for approval in self._items.values():
            if approval.source_session_id == session_id and approval.intent_hash == intent_hash and approval.status == 'pending':
                self._items[approval.id] = approval.model_copy(update={'status': 'rejected'})

    def stats(self) -> dict[str, int]:
        counts = {'pending': 0, 'approved': 0, 'rejected': 0, 'total': 0}
        for item in self._items.values():
            counts[item.status] += 1
            counts['total'] += 1
        return counts
