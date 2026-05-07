from __future__ import annotations

from datetime import UTC, datetime
from threading import Lock
from typing import Any
from uuid import uuid4

from backend.models.schemas import BookingResponse


class MemoryBookingRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: dict[str, dict[str, Any]] = {}

    def count_booking_codes_for_day(self, yyyymmdd: str) -> int:
        prefix = f"BK-{yyyymmdd}-"
        with self._lock:
            return sum(1 for r in self._rows.values() if str(r.get("booking_code", "")).startswith(prefix))

    def insert(self, row: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            bid = str(row.get("id") or uuid4())
            now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            full = {
                **row,
                "id": bid,
                "created_at": row.get("created_at", now),
                "updated_at": row.get("updated_at", now),
            }
            self._rows[bid] = full
            return full.copy()

    def get(self, booking_id: str) -> dict[str, Any] | None:
        with self._lock:
            r = self._rows.get(booking_id)
            return r.copy() if r else None

    def update(self, booking_id: str, patch: dict[str, Any]) -> dict[str, Any] | None:
        with self._lock:
            cur = self._rows.get(booking_id)
            if cur is None:
                return None
            now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
            updated = {**cur, **patch, "updated_at": now}
            self._rows[booking_id] = updated
            return updated.copy()

    def list(self, user_id: str | None, status: str | None) -> list[dict[str, Any]]:
        with self._lock:
            rows = list(self._rows.values())
        if user_id:
            rows = [r for r in rows if r.get("user_id") == user_id]
        if status:
            rows = [r for r in rows if r.get("status") == status]
        rows.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return [r.copy() for r in rows]

    def to_response(self, row: dict[str, Any]) -> BookingResponse:
        return BookingResponse(
            id=row["id"],
            booking_code=row["booking_code"],
            user_id=row["user_id"],
            topic=row["topic"],
            scheduled_at=row["scheduled_at"],
            duration_minutes=row["duration_minutes"],
            status=row["status"],
            calendar_event_id=row.get("calendar_event_id"),
            approval_id=row["approval_id"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            previous_scheduled_at=row.get("previous_scheduled_at"),
        )


class MemoryBookingEmailRepository:
    def __init__(self) -> None:
        self._lock = Lock()
        self._rows: list[dict[str, Any]] = []

    def find(
        self,
        booking_id: str,
        status_at_send: str,
        recipient_role: str,
    ) -> dict[str, Any] | None:
        with self._lock:
            for existing in self._rows:
                if (
                    existing["booking_id"] == booking_id
                    and existing["status_at_send"] == status_at_send
                    and existing["recipient_role"] == recipient_role
                ):
                    return existing.copy()
        return None

    def append(self, row: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._rows.append(row.copy())
            return row.copy()

    def update_by_idempotency(
        self,
        idempotency_key: str,
        patch: dict[str, Any],
    ) -> None:
        with self._lock:
            for r in self._rows:
                if r.get("idempotency_key") == idempotency_key:
                    r.update(patch)
                    return

    def list_for_booking(self, booking_id: str) -> list[dict[str, Any]]:
        with self._lock:
            return [r.copy() for r in self._rows if r["booking_id"] == booking_id]
