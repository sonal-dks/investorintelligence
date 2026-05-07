from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from backend.main import app
from backend.routers.pulse_router import reset_state_for_tests, seed_reviews_for_tests


def _seed_reviews(n: int) -> list[dict]:
    now = datetime.now(UTC).date()
    reviews = []
    for i in range(n):
        reviews.append(
            {
                "reviewer_name": f"User{i}",
                "rating": 5 if i % 3 else 2,
                "review_text": "Portfolio loading is slow and SIP flow is confusing.",
                "review_date": (now - timedelta(days=i % 5)).isoformat(),
            }
        )
    return reviews


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["phase"] == "09-weekly-pulse"


def test_generate_requires_admin():
    reset_state_for_tests()
    seed_reviews_for_tests(_seed_reviews(20))
    c = TestClient(app)
    r = c.post("/api/pulse/generate", headers={"x-user-role": "investor"})
    assert r.status_code == 403


def test_full_pulse_flow():
    reset_state_for_tests()
    seed_reviews_for_tests(_seed_reviews(20))
    c = TestClient(app)
    rg = c.post("/api/pulse/generate", headers={"x-user-role": "admin"})
    assert rg.status_code == 200, rg.text
    judge = rg.json()["judge"]
    assert judge["pass"] is True

    latest = c.get("/api/pulse/latest")
    assert latest.status_code == 200
    body = latest.json()
    assert body["total_reviews"] >= 10
    assert len(body["action_items"]) == 3
    assert "deterministic_summary_text" in body
    assert "deterministic_algorithm" in body
    assert body["themes"] == body["llm_themes"]

    reviews = c.get("/api/pulse/reviews", params={"sentiment": "positive", "page": 1, "limit": 5})
    assert reviews.status_code == 200
    assert reviews.json()["page"] == 1

    keywords = c.get("/api/pulse/keywords")
    assert keywords.status_code == 200
    assert isinstance(keywords.json()["keywords"], list)

    trends = c.get("/api/pulse/trends")
    assert trends.status_code == 200
    assert isinstance(trends.json()["trends"], list)


def test_low_review_week_marked_explicitly():
    reset_state_for_tests()
    seed_reviews_for_tests(_seed_reviews(3))
    c = TestClient(app)
    rg = c.post("/api/pulse/generate", headers={"x-user-role": "admin"})
    assert rg.status_code == 200
    latest = c.get("/api/pulse/latest")
    assert latest.status_code == 200
    assert "Insufficient data" in latest.json()["summary_text"]
