"""Run MCP server: PYTHONPATH=. python -m backend.mcp_action_server.server (from phase-08-calendar-booking)."""

from __future__ import annotations

from fastmcp import FastMCP

from backend.mcp_action_server.bridge import McpBridge

_bridge = McpBridge()
mcp = FastMCP("Next Leap Phase 08 Actions")


@mcp.tool(name="calendar.check_availability")
def calendar_check_availability(
    approval_id: str,
    actor_id: str,
    idempotency_key: str,
    date: str,
    duration_minutes: int,
) -> list[dict[str, str]]:
    return _bridge.calendar_check_availability(
        approval_id, actor_id, idempotency_key, date, duration_minutes
    )


@mcp.tool(name="calendar.create_event")
def calendar_create_event(
    approval_id: str,
    actor_id: str,
    idempotency_key: str,
    title: str,
    start_iso: str,
    end_iso: str,
    event_status: str,
    booking_code: str,
) -> str:
    return _bridge.calendar_create_event(
        approval_id,
        actor_id,
        idempotency_key,
        title,
        start_iso,
        end_iso,
        event_status,
        booking_code,
    )


@mcp.tool(name="calendar.update_event")
def calendar_update_event(
    approval_id: str,
    actor_id: str,
    idempotency_key: str,
    event_id: str,
    start_iso: str | None,
    end_iso: str | None,
    event_status: str | None,
) -> str:
    return _bridge.calendar_update_event(
        approval_id,
        actor_id,
        idempotency_key,
        event_id,
        start_iso,
        end_iso,
        event_status,
    )


@mcp.tool(name="calendar.cancel_event")
def calendar_cancel_event(
    approval_id: str,
    actor_id: str,
    idempotency_key: str,
    event_id: str,
) -> dict[str, bool]:
    return _bridge.calendar_cancel_event(
        approval_id, actor_id, idempotency_key, event_id
    )


@mcp.tool(name="gmail.send")
def gmail_send(
    approval_id: str,
    actor_id: str,
    idempotency_key: str,
    to: list[str],
    subject: str,
    body_markdown: str,
    body_html: str,
    attachments: list[dict] | None = None,
) -> str:
    return _bridge.gmail_send(
        approval_id,
        actor_id,
        idempotency_key,
        to,
        subject,
        body_markdown,
        body_html,
        attachments,
    )


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
