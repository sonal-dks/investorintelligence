from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

BookingStatus = Literal["pending", "confirmed", "cancelled", "rescheduled", "pending_calendar"]
RecipientRole = Literal["user", "advisor"]
SendStatus = Literal["sent", "failed"]


class Slot(BaseModel):
    start: str
    end: str


class BookingCreateRequest(BaseModel):
    user_id: str
    topic: str
    scheduled_at: str
    duration_minutes: int = Field(..., ge=1, le=480)
    approval_id: str


class BookingResponse(BaseModel):
    id: str
    booking_code: str
    user_id: str
    topic: str
    scheduled_at: str
    duration_minutes: int
    status: BookingStatus
    calendar_event_id: str | None
    approval_id: str
    created_at: str
    updated_at: str
    previous_scheduled_at: str | None = None


class BookingRescheduleRequest(BaseModel):
    scheduled_at: str
    duration_minutes: int | None = Field(default=None, ge=1, le=480)


class SendEmailResponseSend(BaseModel):
    recipient_role: RecipientRole
    recipient_email: str
    gmail_message_id: str | None
    deduped: bool


class SendEmailResponse(BaseModel):
    booking_id: str
    status_at_send: str
    sends: list[SendEmailResponseSend]
    pulse_included: bool


class BookingEmailHistoryItem(BaseModel):
    status_at_send: str
    recipient_role: RecipientRole
    recipient_email: str
    subject: str
    sent_at: str
    gmail_message_id: str | None
    sent_by: str
    idempotency_key: str


class BookingEmailHistoryResponse(BaseModel):
    booking_id: str
    history: list[BookingEmailHistoryItem]


class WeeklyPulseSnapshot(BaseModel):
    week_start: str | None
    summary_text: str
    action_items: list[str]
    themes: list[dict]
    generated_at: str
    judge_overall_score: float = 0.0
    judge_metrics: dict = Field(default_factory=dict)
    doc_url: str | None = None
    fee_scenario: str | None = None
    explanation_bullets: list[str] = Field(default_factory=list)
