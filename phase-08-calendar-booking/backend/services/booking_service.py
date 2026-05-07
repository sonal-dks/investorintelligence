from __future__ import annotations

import re
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING
from uuid import uuid4
from zoneinfo import ZoneInfo

from backend.mcp_action_server.bridge import McpBridge
from backend.repositories.memory import MemoryBookingRepository
from backend.services.booking_code_generator import next_booking_code

if TYPE_CHECKING:
    pass

IST = ZoneInfo("Asia/Kolkata")


def parse_iso_dt(s: str) -> datetime:
    s2 = s.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s2)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=IST)
    return dt.astimezone(UTC)


class BookingService:
    def __init__(self, repo: MemoryBookingRepository, mcp: McpBridge) -> None:
        self._repo = repo
        self._mcp = mcp

    def _now_utc(self) -> datetime:
        return datetime.now(UTC)

    def create_booking(
        self,
        *,
        user_id: str,
        topic: str,
        scheduled_at: str,
        duration_minutes: int,
        approval_id: str,
        actor_id: str,
    ):
        start = parse_iso_dt(scheduled_at)
        if start <= self._now_utc():
            raise ValueError("scheduled_at must be in the future")

        code = next_booking_code(self._repo.count_booking_codes_for_day)
        end = start + timedelta(minutes=duration_minutes)
        start_ist = start.astimezone(IST)
        end_ist = end.astimezone(IST)
        title = f"Booking {code}"

        event_id: str | None = None
        status: str = "pending"
        try:
            event_id = self._mcp.calendar_create_event(
                approval_id=approval_id,
                actor_id=actor_id,
                idempotency_key=f"calendar:create:{approval_id}:{code}",
                title=title,
                start_iso=start_ist.isoformat(),
                end_iso=end_ist.isoformat(),
                event_status="tentative",
                booking_code=code,
            )
        except Exception:
            status = "pending_calendar"

        row = {
            "id": str(uuid4()),
            "user_id": user_id,
            "booking_code": code,
            "topic": topic,
            "scheduled_at": start.isoformat().replace("+00:00", "Z"),
            "duration_minutes": duration_minutes,
            "status": status,
            "calendar_event_id": event_id,
            "approval_id": approval_id,
            "previous_scheduled_at": None,
        }
        saved = self._repo.insert(row)
        return self._repo.to_response(saved)

    def confirm(self, booking_id: str, *, approval_id: str, actor_id: str):
        row = self._repo.get(booking_id)
        if row is None:
            return None
        if row["status"] not in ("pending", "pending_calendar"):
            raise ValueError("Booking cannot be confirmed from this state")

        event_id = row.get("calendar_event_id")
        if not event_id:
            start = parse_iso_dt(row["scheduled_at"])
            dur = row["duration_minutes"]
            end = start + timedelta(minutes=dur)
            start_ist = start.astimezone(IST)
            end_ist = end.astimezone(IST)
            title = f"Booking {row['booking_code']}"
            event_id = self._mcp.calendar_create_event(
                approval_id=approval_id,
                actor_id=actor_id,
                idempotency_key=f"calendar:create_on_confirm:{booking_id}",
                title=title,
                start_iso=start_ist.isoformat(),
                end_iso=end_ist.isoformat(),
                event_status="confirmed",
                booking_code=row["booking_code"],
            )
            self._repo.update(booking_id, {"calendar_event_id": event_id})
            row = self._repo.get(booking_id) or row
        else:
            self._mcp.calendar_update_event(
                approval_id=approval_id,
                actor_id=actor_id,
                idempotency_key=f"calendar:confirm:{booking_id}",
                event_id=event_id,
                start_iso=None,
                end_iso=None,
                event_status="confirmed",
            )
        updated = self._repo.update(booking_id, {"status": "confirmed"})
        return self._repo.to_response(updated) if updated else None

    def cancel(self, booking_id: str, *, approval_id: str, actor_id: str):
        row = self._repo.get(booking_id)
        if row is None:
            return None
        if row["status"] == "cancelled":
            return self._repo.to_response(row)
        event_id = row.get("calendar_event_id")
        if event_id:
            self._mcp.calendar_cancel_event(
                approval_id=approval_id,
                actor_id=actor_id,
                idempotency_key=f"calendar:cancel:{booking_id}",
                event_id=event_id,
            )
        updated = self._repo.update(booking_id, {"status": "cancelled"})
        return self._repo.to_response(updated) if updated else None

    def reschedule(
        self,
        booking_id: str,
        *,
        scheduled_at: str,
        duration_minutes: int | None,
        approval_id: str,
        actor_id: str,
    ):
        row = self._repo.get(booking_id)
        if row is None:
            return None
        if row["status"] == "cancelled":
            raise ValueError("Cannot reschedule a cancelled booking")

        new_start = parse_iso_dt(scheduled_at)
        if new_start <= self._now_utc():
            raise ValueError("scheduled_at must be in the future")

        dur = duration_minutes if duration_minutes is not None else row["duration_minutes"]
        new_end = new_start + timedelta(minutes=dur)
        start_ist = new_start.astimezone(IST)
        end_ist = new_end.astimezone(IST)

        event_id = row.get("calendar_event_id")
        if event_id:
            self._mcp.calendar_update_event(
                approval_id=approval_id,
                actor_id=actor_id,
                idempotency_key=f"calendar:reschedule:{booking_id}:{new_start.isoformat()}",
                event_id=event_id,
                start_iso=start_ist.isoformat(),
                end_iso=end_ist.isoformat(),
                event_status=None,
            )

        patch = {
            "scheduled_at": new_start.isoformat().replace("+00:00", "Z"),
            "duration_minutes": dur,
            "status": "rescheduled",
            "previous_scheduled_at": row["scheduled_at"],
        }
        updated = self._repo.update(booking_id, patch)
        return self._repo.to_response(updated) if updated else None

    def get(self, booking_id: str):
        row = self._repo.get(booking_id)
        return self._repo.to_response(row) if row else None

    def list(self, user_id: str | None, status: str | None):
        return [self._repo.to_response(r) for r in self._repo.list(user_id, status)]
