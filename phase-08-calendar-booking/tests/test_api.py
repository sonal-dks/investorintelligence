from __future__ import annotations

from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from backend.deps import reset_stores_for_tests
from backend.main import app


def test_health():
    c = TestClient(app)
    r = c.get("/health")
    assert r.status_code == 200
    assert r.json()["phase"] == "08-calendar-booking"


def test_booking_api_flow():
    reset_stores_for_tests()
    c = TestClient(app)
    headers = {"x-user-role": "admin"}
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat().replace("+00:00", "Z")
    r = c.post(
        "/api/bookings",
        headers=headers,
        json={
            "user_id": "00000000-0000-0000-0000-000000000001",
            "topic": "ELSS",
            "scheduled_at": start,
            "duration_minutes": 30,
            "approval_id": "approval-test-1",
        },
    )
    assert r.status_code == 200, r.text
    bid = r.json()["id"]

    r2 = c.patch(
        f"/api/bookings/{bid}/confirm",
        params={"approval_id": "approval-test-1"},
        headers=headers,
    )
    assert r2.status_code == 200

    r3 = c.post(
        f"/api/bookings/{bid}/send-email",
        headers=headers,
    )
    assert r3.status_code == 200
    body = r3.json()
    assert body["pulse_included"] in (True, False)
    assert len(body["sends"]) == 2

    r4 = c.post(
        f"/api/bookings/{bid}/send-email",
        headers=headers,
    )
    assert r4.status_code == 200
    assert all(s["deduped"] for s in r4.json()["sends"])


def test_non_admin_rejected():
    reset_stores_for_tests()
    c = TestClient(app)
    start = (datetime.now(UTC) + timedelta(days=2)).isoformat().replace("+00:00", "Z")
    r = c.post(
        "/api/bookings",
        headers={"x-user-role": "investor"},
        json={
            "user_id": "u",
            "topic": "t",
            "scheduled_at": start,
            "duration_minutes": 30,
            "approval_id": "a",
        },
    )
    assert r.status_code == 403
