# Phase 08 — Google Calendar + Booking

Implements [Docs/Architecture/architecture.md](../Docs/Architecture/architecture.md) Phase 08: FastMCP tool layer for Calendar + Gmail, booking REST API, booking-confirmation email with template from `Docs/Architecture/Email-Templates/booking_confirmation_email.md`.

## Layout

- `backend/` — FastAPI app (`main.py`), routers, services, in-memory repos (swap for Supabase in assembly).
- `backend/mcp_action_server/` — `bridge.py` (metadata + idempotency), `tools/` (Calendar + Gmail), `server.py` (FastMCP stdio server).
- `migrations/` — Supabase SQL for `bookings` and `booking_emails`.
- `frontend/` — React demo: Calendar tab + booking actions (integrate into Approval Center in Phase 12).
- `tests/` — pytest (service, API, template, email dedupe).

## Quick start

```bash
cd phase-08-calendar-booking
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit values
PYTHONPATH=. pytest tests/ -v
PYTHONPATH=. uvicorn backend.main:app --reload --port 8090
```

## Environment

See `.env.example`. With no `PHASE08_USE_MOCK_*` vars, the app defaults to **live** Google APIs when credentials exist. **Pytest** still forces mocks via `tests/conftest.py`.

### Calendar (service account)

- `GOOGLE_SERVICE_ACCOUNT_JSON` → path to `googleserviceaccount.json`.
- `GOOGLE_CALENDAR_ID` → often your Gmail address **after** you share that calendar with the service account `client_email` (from the JSON) with **Make changes to events**.
- If the API returns **404 Not Found**, create a **secondary calendar** in Google Calendar, share it with the SA, and put that calendar’s ID in `GOOGLE_CALENDAR_ID`.

### Gmail (OAuth user — cannot be automated without your browser)

1. Enable **Gmail API** in GCP.
2. OAuth **Web client** → **Authorized redirect URIs** → add `http://localhost:8765/`
3. Run: `PYTHONPATH=. ./venv/bin/python scripts/gmail_oauth_refresh_token.py`
4. Paste `GMAIL_REFRESH_TOKEN=...` into `.env`.

### Smoke test (one event + one draft)

```bash
PYTHONPATH=. ./venv/bin/python scripts/smoke_calendar_and_draft.py
```


## Integration notes

- **Phase 07:** After admin approves a booking-type approval, call `POST /api/bookings` with `approval_id` and payload fields (or merge routers in a single ASGI app in Phase 12).
- **Phase 09:** When `weekly_pulse` exists in Supabase, booking emails include the pulse block; otherwise a footnote is inserted automatically.
