"""Request/response schemas for dashboard API."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel

RoleLiteral = Literal["investor", "admin"]
TrendDirection = Literal["up", "down", "neutral", "new"]


class KPIItem(BaseModel):
    value: int
    trend_pct: float
    trend_direction: TrendDirection


class KPIResponse(BaseModel):
    login_sessions: KPIItem
    chatbot_sessions: KPIItem
    voice_sessions: KPIItem
    bookings: KPIItem


class BookingSummaryResponse(BaseModel):
    confirmed: int
    cancelled: int
    rescheduled: int
    total: int


class FundRow(BaseModel):
    fund_name: str
    category: str
    nav: float
    nav_date: date | None


class FundStripResponse(BaseModel):
    funds: list[FundRow]
    last_scraped_at: str | None


class PulsePreviewResponse(BaseModel):
    overall_rating: float
    new_reviews_this_week: int
    sentiment_summary: str
