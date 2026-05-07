from __future__ import annotations

from backend.mcp_action_server.bridge import McpBridge
from backend.repositories.memory import MemoryBookingEmailRepository, MemoryBookingRepository
from backend.services.booking_email_service import BookingEmailService
from backend.services.booking_service import BookingService
from backend.services.email_template_renderer import EmailTemplateRenderer

import backend.config as cfg

_bookings_repo = MemoryBookingRepository()
_emails_repo = MemoryBookingEmailRepository()
_mcp_bridge = McpBridge()


def reset_stores_for_tests() -> None:
    """Reset in-memory state and MCP idempotency cache (for pytest)."""
    global _bookings_repo, _emails_repo, _mcp_bridge
    cfg.use_mock_calendar.cache_clear()
    cfg.use_mock_gmail.cache_clear()
    _bookings_repo = MemoryBookingRepository()
    _emails_repo = MemoryBookingEmailRepository()
    _mcp_bridge = McpBridge()


def get_mcp_bridge() -> McpBridge:
    return _mcp_bridge


def get_booking_service() -> BookingService:
    return BookingService(_bookings_repo, _mcp_bridge)


def get_email_renderer() -> EmailTemplateRenderer:
    return EmailTemplateRenderer(cfg.resolved_template_path())


def get_email_service() -> BookingEmailService:
    return BookingEmailService(
        _bookings_repo,
        _emails_repo,
        _mcp_bridge,
        get_email_renderer(),
    )
