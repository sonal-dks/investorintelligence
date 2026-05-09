from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app


def test_health():
    client = TestClient(app)
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["phase"] == "10-explorer"


def test_get_funds_and_summary():
    client = TestClient(app)
    resp = client.get("/api/funds")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["funds"]) >= 30
    assert body["summary"]["tracked_funds"] == len(body["funds"])

    summary = client.get("/api/funds/summary")
    assert summary.status_code == 200
    assert "avg_expense_ratio" in summary.json()
