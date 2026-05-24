from __future__ import annotations

from typing import Any, Callable

from backend.mcp_action_server.tools import calendar_impl, gmail_impl


def _require_meta(approval_id: str, actor_id: str, idempotency_key: str) -> None:
    if not approval_id or not approval_id.strip():
        raise ValueError("approval_id is required for MCP tool calls")
    if not actor_id or not actor_id.strip():
        raise ValueError("actor_id is required for MCP tool calls")
    if not idempotency_key or not idempotency_key.strip():
        raise ValueError("idempotency_key is required for MCP tool calls")


class McpBridge:
    """Invokes the same implementations as the FastMCP server, with metadata validation and tool-level idempotency."""

    def __init__(self) -> None:
        self._idempotent_cache: dict[tuple[str, str], Any] = {}

    def _cached(self, tool: str, idempotency_key: str, fn: Callable[[], Any]) -> Any:
        key = (tool, idempotency_key)
        if key in self._idempotent_cache:
            return self._idempotent_cache[key]
        out = fn()
        self._idempotent_cache[key] = out
        return out

    def calendar_check_availability(
        self,
        approval_id: str,
        actor_id: str,
        idempotency_key: str,
        date: str,
        duration_minutes: int,
    ) -> list[dict[str, str]]:
        _require_meta(approval_id, actor_id, idempotency_key)
        return self._cached(
            "calendar.check_availability",
            idempotency_key,
            lambda: calendar_impl.check_availability_impl(date, duration_minutes),
        )

    def calendar_create_event(
        self,
        approval_id: str,
        actor_id: str,
        idempotency_key: str,
        title: str,
        start_iso: str,
        end_iso: str,
        event_status: str,
        booking_code: str,
    ) -> str:
        _require_meta(approval_id, actor_id, idempotency_key)
        return self._cached(
            "calendar.create_event",
            idempotency_key,
            lambda: calendar_impl.create_event_impl(
                title, start_iso, end_iso, event_status, booking_code
            ),
        )

    def calendar_update_event(
        self,
        approval_id: str,
        actor_id: str,
        idempotency_key: str,
        event_id: str,
        start_iso: str | None,
        end_iso: str | None,
        event_status: str | None,
    ) -> str:
        _require_meta(approval_id, actor_id, idempotency_key)
        return self._cached(
            "calendar.update_event",
            idempotency_key,
            lambda: calendar_impl.update_event_impl(
                event_id, start_iso, end_iso, event_status
            ),
        )

    def calendar_cancel_event(
        self,
        approval_id: str,
        actor_id: str,
        idempotency_key: str,
        event_id: str,
    ) -> dict[str, bool]:
        _require_meta(approval_id, actor_id, idempotency_key)
        return self._cached(
            "calendar.cancel_event",
            idempotency_key,
            lambda: calendar_impl.cancel_event_impl(event_id),
        )

    def gmail_send(
        self,
        approval_id: str,
        actor_id: str,
        idempotency_key: str,
        to: list[str],
        subject: str,
        body_markdown: str,
        body_html: str,
        attachments: list[dict] | None = None,
    ) -> str:
        _require_meta(approval_id, actor_id, idempotency_key)
        return self._cached(
            "gmail.send",
            idempotency_key,
            lambda: gmail_impl.send_gmail_impl(
                to, subject, body_markdown, body_html, idempotency_key, attachments=attachments
            ),
        )
