"""Dashboard data service."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from supabase import Client, create_client

from backend.config import Settings
from backend.models.schemas import (
    BookingSummaryResponse,
    FundRow,
    FundStripResponse,
    KPIItem,
    KPIResponse,
    PulsePreviewResponse,
    RoleLiteral,
)


def _to_float(value: Any) -> float:
    if value is None:
        return 0.0
    return float(value)


def _safe_int(value: Any) -> int:
    if value is None:
        return 0
    return int(value)


def calc_trend(current_value: int, previous_value: int) -> tuple[float, str]:
    if previous_value == 0:
        if current_value > 0:
            return 100.0, "new"
        return 0.0, "neutral"
    pct = round(((current_value - previous_value) / previous_value) * 100, 2)
    if pct > 0:
        return pct, "up"
    if pct < 0:
        return pct, "down"
    return 0.0, "neutral"


class DashboardService:
    def __init__(self, settings: Settings) -> None:
        self._client: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)

    def _resolve_role(self, user_id: str) -> RoleLiteral:
        result = (
            self._client.table("user_profiles")
            .select("role")
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )
        rows = result.data or []
        if not rows:
            return "investor"
        role = rows[0].get("role")
        return "admin" if role == "admin" else "investor"

    def _count_activity(self, event_type: str, start_iso: str, end_iso: str, user_id: str, role: RoleLiteral) -> int:
        query = (
            self._client.table("activity_log")
            .select("id", count="exact")
            .eq("event_type", event_type)
            .gte("created_at", start_iso)
            .lt("created_at", end_iso)
        )
        if role == "investor":
            query = query.eq("user_id", user_id)
        result = query.execute()
        return int(result.count or 0)

    def _count_bookings(self, start_iso: str, end_iso: str, user_id: str, role: RoleLiteral) -> int:
        query = (
            self._client.table("bookings")
            .select("id", count="exact")
            .gte("created_at", start_iso)
            .lt("created_at", end_iso)
        )
        if role == "investor":
            query = query.eq("user_id", user_id)
        result = query.execute()
        return int(result.count or 0)

    def get_kpis(self, user_id: str) -> KPIResponse:
        role = self._resolve_role(user_id)
        now = datetime.now(UTC)
        current_start = now - timedelta(days=7)
        previous_start = now - timedelta(days=14)

        current_start_iso = current_start.isoformat()
        previous_start_iso = previous_start.isoformat()
        now_iso = now.isoformat()

        mapping = {
            "login_sessions": "login",
            "chatbot_sessions": "chatbot_used",
            "voice_sessions": "voice_agent_used",
        }

        response_data: dict[str, KPIItem] = {}
        for key, event_type in mapping.items():
            current_count = self._count_activity(event_type, current_start_iso, now_iso, user_id, role)
            previous_count = self._count_activity(
                event_type, previous_start_iso, current_start_iso, user_id, role
            )
            trend_pct, trend_direction = calc_trend(current_count, previous_count)
            response_data[key] = KPIItem(
                value=current_count,
                trend_pct=trend_pct,
                trend_direction=trend_direction,
            )

        booking_current = self._count_bookings(current_start_iso, now_iso, user_id, role)
        booking_prev = self._count_bookings(previous_start_iso, current_start_iso, user_id, role)
        booking_pct, booking_dir = calc_trend(booking_current, booking_prev)
        response_data["bookings"] = KPIItem(
            value=booking_current,
            trend_pct=booking_pct,
            trend_direction=booking_dir,
        )
        return KPIResponse(**response_data)

    def get_booking_summary(self, user_id: str) -> BookingSummaryResponse:
        role = self._resolve_role(user_id)
        query = self._client.table("bookings").select("status")
        if role == "investor":
            query = query.eq("user_id", user_id)
        rows = query.execute().data or []
        status_counts = {"confirmed": 0, "cancelled": 0, "rescheduled": 0}
        for row in rows:
            status = row.get("status")
            if status in status_counts:
                status_counts[status] += 1
        return BookingSummaryResponse(
            confirmed=status_counts["confirmed"],
            cancelled=status_counts["cancelled"],
            rescheduled=status_counts["rescheduled"],
            total=sum(status_counts.values()),
        )

    def get_fund_strip(self) -> FundStripResponse:
        rows = (
            self._client.table("mutual_fund_data")
            .select("fund_slug,fund_name,category,nav,nav_date,scraped_at")
            .order("fund_slug")
            .order("scraped_at", desc=True)
            .execute()
            .data
            or []
        )
        latest_by_slug: dict[str, dict[str, Any]] = {}
        for row in rows:
            slug = row.get("fund_slug")
            if isinstance(slug, str) and slug not in latest_by_slug:
                latest_by_slug[slug] = row
        funds = [
            FundRow(
                fund_name=str(row.get("fund_name") or "Unknown"),
                category=str(row.get("category") or "Unknown"),
                nav=_to_float(row.get("nav")),
                nav_date=row.get("nav_date"),
            )
            for row in latest_by_slug.values()
        ]
        funds.sort(key=lambda r: r.fund_name.lower())
        last_scraped_at = max((row.get("scraped_at") for row in latest_by_slug.values()), default=None)
        return FundStripResponse(funds=funds, last_scraped_at=last_scraped_at)

    def get_pulse_preview(self) -> PulsePreviewResponse:
        rows = (
            self._client.table("app_reviews")
            .select("rating,review_text,review_date")
            .order("review_date", desc=True)
            .limit(200)
            .execute()
            .data
            or []
        )
        if not rows:
            return PulsePreviewResponse(
                overall_rating=0.0,
                new_reviews_this_week=0,
                sentiment_summary="No weekly pulse data yet",
            )

        rating_sum = sum(_safe_int(r.get("rating")) for r in rows)
        overall_rating = round(rating_sum / len(rows), 2)
        week_start = datetime.now(UTC).date() - timedelta(days=datetime.now(UTC).weekday())
        new_reviews_this_week = sum(
            1
            for row in rows
            if row.get("review_date") and datetime.fromisoformat(str(row["review_date"])).date() >= week_start
        )
        sentiment_summary = "Mixed sentiment this week"
        if overall_rating >= 4.0:
            sentiment_summary = "Positive sentiment trend"
        elif overall_rating <= 2.5:
            sentiment_summary = "Negative sentiment trend"
        return PulsePreviewResponse(
            overall_rating=overall_rating,
            new_reviews_this_week=new_reviews_this_week,
            sentiment_summary=sentiment_summary,
        )
