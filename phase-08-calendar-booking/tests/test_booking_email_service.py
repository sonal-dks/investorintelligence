from __future__ import annotations

from datetime import UTC, datetime, timedelta

from backend.mcp_action_server.bridge import McpBridge
from backend.repositories.memory import MemoryBookingEmailRepository, MemoryBookingRepository
from backend.services.booking_email_service import BookingEmailService
from backend.services.booking_service import BookingService
from backend.services.email_template_renderer import EmailTemplateRenderer

import backend.config as cfg


def _template_path() -> str:
    return cfg.resolved_template_path()


def test_send_email_dedupes_same_status():
    repo = MemoryBookingRepository()
    emails = MemoryBookingEmailRepository()
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
    svc.confirm(b.id, approval_id="ap1", actor_id="admin")

    renderer = EmailTemplateRenderer(_template_path())
    mail = BookingEmailService(repo, emails, mcp, renderer)

    r1 = mail.send_booking_email(b.id, actor_id="admin")
    assert all(not s.deduped for s in r1.sends)

    r2 = mail.send_booking_email(b.id, actor_id="admin")
    assert all(s.deduped for s in r2.sends)


def test_send_email_rejected_when_pending():
    repo = MemoryBookingRepository()
    emails = MemoryBookingEmailRepository()
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
    renderer = EmailTemplateRenderer(_template_path())
    mail = BookingEmailService(repo, emails, mcp, renderer)
    try:
        mail.send_booking_email(b.id, actor_id="admin")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "confirmed" in str(e).lower()
