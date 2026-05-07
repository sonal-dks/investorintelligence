from __future__ import annotations

import json
import os
from datetime import datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo

from backend import config

IST = ZoneInfo("Asia/Kolkata")
UTC = ZoneInfo("UTC")


def _load_sa_credentials():
    from google.oauth2 import service_account

    raw = config.google_service_account_json()
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not set")
    if os.path.isfile(raw):
        return service_account.Credentials.from_service_account_file(
            raw,
            scopes=["https://www.googleapis.com/auth/calendar"],
        )
    info = json.loads(raw)
    return service_account.Credentials.from_service_account_info(
        info,
        scopes=["https://www.googleapis.com/auth/calendar"],
    )


def _calendar_service():
    from googleapiclient.discovery import build

    creds = _load_sa_credentials()
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def check_availability_impl(date_iso: str, duration_minutes: int) -> list[dict[str, str]]:
    """Return available slots as {start,end} ISO strings (with offset)."""
    if config.use_mock_calendar():
        return _mock_slots(date_iso, duration_minutes)

    cal_id = config.google_calendar_id()
    if not cal_id:
        raise RuntimeError("GOOGLE_CALENDAR_ID not set")

    day = datetime.fromisoformat(date_iso).date()
    start_local = datetime.combine(day, datetime.min.time().replace(hour=0, minute=0), tzinfo=IST)
    end_local = start_local + timedelta(days=1)
    time_min = start_local.astimezone(UTC).isoformat().replace("+00:00", "Z")
    time_max = end_local.astimezone(UTC).isoformat().replace("+00:00", "Z")

    service = _calendar_service()
    body = {
        "timeMin": time_min,
        "timeMax": time_max,
        "items": [{"id": cal_id}],
    }
    fb = service.freebusy().query(body=body).execute()
    busy_raw = fb.get("calendars", {}).get(cal_id, {}).get("busy", [])

    busy: list[tuple[datetime, datetime]] = []
    for b in busy_raw:
        bs = datetime.fromisoformat(b["start"].replace("Z", "+00:00"))
        be = datetime.fromisoformat(b["end"].replace("Z", "+00:00"))
        busy.append((bs, be))

    slots: list[dict[str, str]] = []
    work_start = start_local.replace(hour=10, minute=0, second=0, microsecond=0)
    work_end = start_local.replace(hour=17, minute=0, second=0, microsecond=0)
    step = timedelta(minutes=30)
    cur = work_start
    while cur + timedelta(minutes=duration_minutes) <= work_end:
        slot_start = cur.astimezone(UTC)
        slot_end = (cur + timedelta(minutes=duration_minutes)).astimezone(UTC)
        conflict = any(
            not (slot_end <= b0 or slot_start >= b1)
            for b0, b1 in busy
        )
        if not conflict:
            slots.append(
                {
                    "start": cur.isoformat(),
                    "end": (cur + timedelta(minutes=duration_minutes)).isoformat(),
                }
            )
        cur += step
    return slots


def _mock_slots(date_iso: str, duration_minutes: int) -> list[dict[str, str]]:
    day = datetime.fromisoformat(date_iso).date()
    base = datetime.combine(day, datetime.min.time().replace(hour=10, minute=0), tzinfo=IST)
    out: list[dict[str, str]] = []
    for h in (10, 14, 16):
        s = base.replace(hour=h)
        e = s + timedelta(minutes=duration_minutes)
        out.append({"start": s.isoformat(), "end": e.isoformat()})
    return out


def create_event_impl(
    title: str,
    start_iso: str,
    end_iso: str,
    event_status: str,
    booking_code: str,
) -> str:
    if config.use_mock_calendar():
        return f"mock-cal-event-{booking_code}"

    cal_id = config.google_calendar_id()
    if not cal_id:
        raise RuntimeError("GOOGLE_CALENDAR_ID not set")

    service = _calendar_service()
    body: dict[str, Any] = {
        "summary": title,
        "description": f"Booking code: {booking_code}",
        "start": {"dateTime": start_iso, "timeZone": "Asia/Kolkata"},
        "end": {"dateTime": end_iso, "timeZone": "Asia/Kolkata"},
        "status": "tentative" if event_status == "tentative" else "confirmed",
    }
    ev = service.events().insert(calendarId=cal_id, body=body).execute()
    return str(ev["id"])


def update_event_impl(
    event_id: str,
    start_iso: str | None,
    end_iso: str | None,
    event_status: str | None,
) -> str:
    if config.use_mock_calendar():
        return event_id

    cal_id = config.google_calendar_id()
    if not cal_id:
        raise RuntimeError("GOOGLE_CALENDAR_ID not set")

    service = _calendar_service()
    patch: dict[str, Any] = {}
    if start_iso:
        patch["start"] = {"dateTime": start_iso, "timeZone": "Asia/Kolkata"}
    if end_iso:
        patch["end"] = {"dateTime": end_iso, "timeZone": "Asia/Kolkata"}
    if event_status:
        patch["status"] = "tentative" if event_status == "tentative" else "confirmed"
    service.events().patch(calendarId=cal_id, eventId=event_id, body=patch).execute()
    return event_id


def cancel_event_impl(event_id: str) -> dict[str, bool]:
    if config.use_mock_calendar():
        return {"ok": True}

    cal_id = config.google_calendar_id()
    if not cal_id:
        raise RuntimeError("GOOGLE_CALENDAR_ID not set")

    service = _calendar_service()
    service.events().delete(calendarId=cal_id, eventId=event_id).execute()
    return {"ok": True}
