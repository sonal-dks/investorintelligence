import pytest

from backend.mcp_action_server.bridge import McpBridge


def test_mcp_rejects_missing_metadata():
    b = McpBridge()
    with pytest.raises(ValueError, match="approval_id"):
        b.calendar_check_availability("", "a", "k", "2026-05-12", 30)
    with pytest.raises(ValueError, match="actor_id"):
        b.calendar_check_availability("ap", "", "k", "2026-05-12", 30)
    with pytest.raises(ValueError, match="idempotency_key"):
        b.calendar_check_availability("ap", "ac", "", "2026-05-12", 30)


def test_mcp_idempotency_returns_cached():
    b = McpBridge()
    r1 = b.calendar_check_availability("ap", "ac", "same", "2026-05-12", 30)
    r2 = b.calendar_check_availability("ap", "ac", "same", "2026-05-13", 30)
    assert r1 == r2  # key ignores date — caller must vary idempotency_key per docs
