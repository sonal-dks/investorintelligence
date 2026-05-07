from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from backend.deps import get_booking_service, get_email_service
from backend.models.schemas import (
    BookingCreateRequest,
    BookingEmailHistoryResponse,
    BookingRescheduleRequest,
    BookingResponse,
    SendEmailResponse,
)

router = APIRouter(prefix="/api/bookings", tags=["phase-08-bookings"])


def _admin_guard(x_user_role: str) -> None:
    if x_user_role.lower() != "admin":
        raise HTTPException(status_code=403, detail="Admin only")


@router.get("/meta/pulse-available")
def pulse_available():
    from backend.services.pulse_fetcher import fetch_latest_pulse

    p = fetch_latest_pulse()
    return {"available": p is not None}


@router.post("", response_model=BookingResponse)
def create_booking(
    body: BookingCreateRequest,
    x_user_role: str = Header(default="investor"),
    actor_id: str = Header(default="api-user"),
):
    _admin_guard(x_user_role)
    svc = get_booking_service()
    try:
        return svc.create_booking(
            user_id=body.user_id,
            topic=body.topic,
            scheduled_at=body.scheduled_at,
            duration_minutes=body.duration_minutes,
            approval_id=body.approval_id,
            actor_id=actor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("", response_model=list[BookingResponse])
def list_bookings(
    user_id: str | None = Query(default=None),
    status: str | None = Query(default=None),
):
    svc = get_booking_service()
    return svc.list(user_id, status)


@router.get("/{booking_id}", response_model=BookingResponse)
def get_booking(booking_id: str):
    svc = get_booking_service()
    b = svc.get(booking_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b


@router.patch("/{booking_id}/confirm", response_model=BookingResponse)
def confirm_booking(
    booking_id: str,
    approval_id: str = Query(...),
    x_user_role: str = Header(default="investor"),
    actor_id: str = Header(default="admin-demo"),
):
    _admin_guard(x_user_role)
    svc = get_booking_service()
    try:
        b = svc.confirm(booking_id, approval_id=approval_id, actor_id=actor_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if b is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b


@router.patch("/{booking_id}/cancel", response_model=BookingResponse)
def cancel_booking(
    booking_id: str,
    approval_id: str = Query(...),
    x_user_role: str = Header(default="investor"),
    actor_id: str = Header(default="admin-demo"),
):
    _admin_guard(x_user_role)
    svc = get_booking_service()
    b = svc.cancel(booking_id, approval_id=approval_id, actor_id=actor_id)
    if b is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b


@router.patch("/{booking_id}/reschedule", response_model=BookingResponse)
def reschedule_booking(
    booking_id: str,
    body: BookingRescheduleRequest,
    approval_id: str = Query(...),
    x_user_role: str = Header(default="investor"),
    actor_id: str = Header(default="admin-demo"),
):
    _admin_guard(x_user_role)
    svc = get_booking_service()
    try:
        b = svc.reschedule(
            booking_id,
            scheduled_at=body.scheduled_at,
            duration_minutes=body.duration_minutes,
            approval_id=approval_id,
            actor_id=actor_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    if b is None:
        raise HTTPException(status_code=404, detail="Booking not found")
    return b


@router.post("/{booking_id}/send-email", response_model=SendEmailResponse)
def send_email(
    booking_id: str,
    notice: int = Query(default=0),
    x_user_role: str = Header(default="investor"),
    actor_id: str = Header(default="admin-demo"),
):
    _admin_guard(x_user_role)
    svc = get_email_service()
    try:
        return svc.send_booking_email(
            booking_id,
            actor_id=actor_id,
            allow_notice=bool(notice),
        )
    except ValueError as e:
        msg = str(e)
        code = 409 if "only for confirmed" in msg else 400
        raise HTTPException(status_code=code, detail=msg) from e
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e


@router.get("/{booking_id}/emails", response_model=BookingEmailHistoryResponse)
def booking_emails_history(
    booking_id: str,
    x_user_role: str = Header(default="investor"),
):
    _admin_guard(x_user_role)
    svc = get_email_service()
    return svc.history(booking_id)
