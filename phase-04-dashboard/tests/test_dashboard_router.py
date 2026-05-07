"""Integration-like tests for dashboard router with dependency overrides."""

import os

from fastapi.testclient import TestClient

os.environ.setdefault("SUPABASE_URL", "https://unit-test.supabase.co")
os.environ.setdefault("SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
os.environ.setdefault("SUPABASE_JWT_SECRET", "unit-test-jwt-secret")

from backend.main import app
from backend.routers.dashboard_router import get_dashboard_service


class StubDashboardService:
    def get_kpis(self, user_id: str) -> dict:
        assert user_id == "user-1"
        return {
            "login_sessions": {"value": 12, "trend_pct": 20.0, "trend_direction": "up"},
            "chatbot_sessions": {"value": 8, "trend_pct": -10.5, "trend_direction": "down"},
            "voice_sessions": {"value": 3, "trend_pct": 100.0, "trend_direction": "new"},
            "bookings": {"value": 2, "trend_pct": 0.0, "trend_direction": "neutral"},
        }

    def get_booking_summary(self, user_id: str) -> dict:
        assert user_id == "user-1"
        return {"confirmed": 5, "cancelled": 2, "rescheduled": 1, "total": 8}

    def get_fund_strip(self) -> dict:
        return {
            "funds": [
                {
                    "fund_name": "Mirae Asset Large Cap Fund",
                    "category": "Large Cap",
                    "nav": 105.43,
                    "nav_date": "2026-05-05",
                }
            ],
            "last_scraped_at": "2026-05-06T06:00:00Z",
        }

    def get_pulse_preview(self) -> dict:
        return {
            "overall_rating": 4.23,
            "new_reviews_this_week": 18,
            "sentiment_summary": "Positive sentiment trend",
        }


def override_user() -> str:
    return "user-1"


def test_dashboard_endpoints() -> None:
    from backend import deps

    app.dependency_overrides[get_dashboard_service] = lambda: StubDashboardService()
    app.dependency_overrides[deps.get_current_user_id] = override_user
    client = TestClient(app)

    kpi = client.get("/api/dashboard/kpis")
    assert kpi.status_code == 200
    assert kpi.json()["login_sessions"]["value"] == 12

    bookings = client.get("/api/dashboard/bookings")
    assert bookings.status_code == 200
    assert bookings.json()["total"] == 8

    fund_strip = client.get("/api/dashboard/fund-strip")
    assert fund_strip.status_code == 200
    assert fund_strip.json()["funds"][0]["fund_name"] == "Mirae Asset Large Cap Fund"

    pulse = client.get("/api/dashboard/pulse-preview")
    assert pulse.status_code == 200
    assert pulse.json()["new_reviews_this_week"] == 18

    app.dependency_overrides.clear()
