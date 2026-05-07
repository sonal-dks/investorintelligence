from __future__ import annotations

from urllib.parse import quote

from fastapi import APIRouter, Header, HTTPException, Query

from backend import config
from backend.deps import get_mcp_bridge

router = APIRouter(prefix="/api/calendar", tags=["phase-08-calendar"])


def _admin_guard(x_user_role: str) -> None:
    if x_user_role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/availability")
def availability(
    date: str = Query(..., description="YYYY-MM-DD"),
    duration: int = Query(30, ge=1, le=480),
    approval_id: str = Query(default="availability-read"),
    actor_id: str = Query(default="api-user"),
    idempotency_key: str = Query(default="availability-default"),
    x_user_role: str = Header(default="investor"),
):
    _admin_guard(x_user_role)
    mcp = get_mcp_bridge()
    try:
        slots = mcp.calendar_check_availability(
            approval_id=approval_id,
            actor_id=actor_id,
            idempotency_key=f"{idempotency_key}:{date}:{duration}",
            date=date,
            duration_minutes=duration,
        )
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Calendar unavailable: {e}") from e
    return {"date": date, "available_slots": slots}


@router.get("/iframe-url")
def iframe_url():
    cid = config.google_calendar_id()
    if not cid:
        return {
            "url": None,
            "message": "Set GOOGLE_CALENDAR_ID for embed URL",
        }
    enc = quote(cid, safe="")
    return {
        "url": f"https://calendar.google.com/calendar/embed?src={enc}",
    }
