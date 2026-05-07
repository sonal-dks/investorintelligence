# Phase 08 — Implementation log

| Step | Check | Result |
|------|--------|--------|
| Backend FastAPI + routers | `PYTHONPATH=. pytest tests/` | PASS |
| MCP bridge + mock calendar/gmail | default `PHASE08_USE_MOCK_*=1` | PASS |
| Booking lifecycle | create → confirm → cancel / reschedule | PASS |
| Email dedupe | second `send-email` returns `deduped: true` | PASS |
| FastMCP server module | `python -m backend.mcp_action_server.server` (stdio) | Manual |

## Run API

```bash
cd phase-08-calendar-booking
source venv/bin/activate  # or ./venv/bin/activate
export PYTHONPATH=.
export PHASE08_USE_MOCK_CALENDAR=1 PHASE08_USE_MOCK_GMAIL=1
export ADVISOR_EMAIL=you@example.com
export PHASE08_TEST_USER_EMAIL=user@example.com
uvicorn backend.main:app --reload --port 8090
```

## Run MCP server (stdio)

```bash
cd phase-08-calendar-booking
PYTHONPATH=. python -m backend.mcp_action_server.server
```

## Live Google Calendar / Gmail

Set `PHASE08_USE_MOCK_CALENDAR=0`, provide `GOOGLE_SERVICE_ACCOUNT_JSON`, `GOOGLE_CALENDAR_ID`.  
Set `PHASE08_USE_MOCK_GMAIL=0`, provide Gmail OAuth env vars per `.env.example`.
