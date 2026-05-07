#!/usr/bin/env python3
"""
Live smoke test: create one Calendar event (service account) + one Gmail draft (OAuth user).

Requires:
  - GOOGLE_SERVICE_ACCOUNT_JSON + GOOGLE_CALENDAR_ID + calendar shared with SA client_email
  - GMAIL_* + GMAIL_REFRESH_TOKEN + GMAIL_FROM_ADDRESS
  - PHASE08_USE_MOCK_CALENDAR=0 and PHASE08_USE_MOCK_GMAIL=0 (or omit; defaults are off)

Run from phase-08-calendar-booking:
  PYTHONPATH=. ./venv/bin/python scripts/smoke_calendar_and_draft.py
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
os.chdir(ROOT)

from dotenv import load_dotenv  # noqa: E402

load_dotenv(ROOT / ".env", override=True)

os.environ["PHASE08_USE_MOCK_CALENDAR"] = "0"
os.environ["PHASE08_USE_MOCK_GMAIL"] = "0"

from backend import config  # noqa: E402

config.use_mock_calendar.cache_clear()
config.use_mock_gmail.cache_clear()

from backend.mcp_action_server.tools import calendar_impl, gmail_impl  # noqa: E402
from zoneinfo import ZoneInfo  # noqa: E402

IST = ZoneInfo("Asia/Kolkata")


def main() -> None:
    start = datetime.now(IST).replace(second=0, microsecond=0) + timedelta(days=1, hours=1)
    start = start.replace(minute=0)
    end = start + timedelta(minutes=30)
    title = f"Phase08 smoke booking {start.strftime('%Y-%m-%d %H:%M IST')}"

    print("1) Creating Calendar event…")
    try:
        eid = calendar_impl.create_event_impl(
            title,
            start.isoformat(),
            end.isoformat(),
            "confirmed",
            "BK-SMOKE-TEST",
        )
        print(f"   OK — event_id={eid}")
        print(f"   Open Google Calendar for {config.google_calendar_id()} to verify.")
    except Exception as e:
        print(f"   FAILED: {e}")
        print(
            "   Share this calendar with the service account email in googleserviceaccount.json\n"
            "   (client_email, e.g. …@….iam.gserviceaccount.com) with “Make changes to events”."
        )

    addr = os.getenv("GMAIL_FROM_ADDRESS") or "kumarsonal100@gmail.com"
    print("\n2) Creating Gmail draft (to same address for testing)…")
    try:
        did = gmail_impl.create_draft_impl(
            to_addresses=[addr],
            subject=f"[Phase08 smoke] {title}",
            body_markdown=f"Smoke test draft.\n\nCalendar title: {title}\n",
            body_html=f"<p>Smoke test draft.</p><p>Calendar title: {title}</p>",
        )
        print(f"   OK — draft_id={did}")
        print("   Open Gmail → Drafts for this account to verify.")
    except Exception as e:
        print(f"   FAILED: {e}")
        print("   Run: PYTHONPATH=. ./venv/bin/python scripts/gmail_oauth_refresh_token.py")
        print("   and set GMAIL_REFRESH_TOKEN in .env")


if __name__ == "__main__":
    main()
