from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.repositories.memory import MemoryBookingRepository
from backend.services.booking_code_generator import next_booking_code
from backend.services.booking_service import BookingService
from backend.mcp_action_server.bridge import McpBridge


def test_booking_code_format():
    repo = MemoryBookingRepository()

    def count(ymd: str) -> int:
        return repo.count_booking_codes_for_day(ymd)

    code = next_booking_code(count)
    assert code.startswith("BK-")
    assert code.count("-") == 2


def test_create_confirm_cancel_flow():
    repo = MemoryBookingRepository()
    mcp = McpBridge()
    svc = BookingService(repo, mcp)
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat().replace("+00:00", "Z")
    b = svc.create_booking(
        user_id="u1",
        topic="ELSS",
        scheduled_at=start,
        duration_minutes=30,
        approval_id="ap1",
        actor_id="admin",
    )
    assert b.status == "pending"
    assert b.calendar_event_id

    c = svc.confirm(b.id, approval_id="ap1", actor_id="admin")
    assert c and c.status == "confirmed"

    x = svc.cancel(b.id, approval_id="ap1", actor_id="admin")
    assert x and x.status == "cancelled"


def test_reschedule_updates_previous():
    repo = MemoryBookingRepository()
    svc = BookingService(repo, McpBridge())
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat().replace("+00:00", "Z")
    b = svc.create_booking(
        user_id="u1",
        topic="Topic",
        scheduled_at=start,
        duration_minutes=30,
        approval_id="ap1",
        actor_id="admin",
    )
    svc.confirm(b.id, approval_id="ap1", actor_id="admin")
    new_start = (datetime.now(UTC) + timedelta(days=3)).isoformat().replace("+00:00", "Z")
    r = svc.reschedule(
        b.id,
        scheduled_at=new_start,
        duration_minutes=45,
        approval_id="ap1",
        actor_id="admin",
    )
    assert r and r.status == "rescheduled"
    assert r.previous_scheduled_at == start


def test_past_booking_rejected():
    repo = MemoryBookingRepository()
    svc = BookingService(repo, McpBridge())
    past = (datetime.now(UTC) - timedelta(days=1)).isoformat().replace("+00:00", "Z")
    try:
        svc.create_booking(
            user_id="u1",
            topic="x",
            scheduled_at=past,
            duration_minutes=30,
            approval_id="ap1",
            actor_id="admin",
        )
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "future" in str(e).lower()
