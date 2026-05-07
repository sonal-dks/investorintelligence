from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


def test_admin_required():
    r = client.post("/api/eval/run", json={"run_type": "manual"})
    assert r.status_code == 403


def test_run_and_latest():
    run = client.post("/api/eval/run", headers={"x-user-role": "admin"}, json={"run_type": "manual"})
    assert run.status_code == 200
    body = run.json()
    assert body["run"]["status"] == "completed"
    latest = client.get("/api/eval/latest")
    assert latest.status_code == 200
