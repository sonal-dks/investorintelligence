"""Tests for voice router endpoints — focused on schema validation and health."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.main import app

client = TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_ok(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["phase"] == "06-voice-agent"


class TestTTSEndpoint:
    def test_tts_requires_nonempty_text(self):
        resp = client.post("/api/voice/tts", json={"text": ""})
        assert resp.status_code == 422

    def test_tts_rejects_over_max_length(self):
        resp = client.post("/api/voice/tts", json={"text": "x" * 1001})
        assert resp.status_code == 422

    def test_tts_valid_request_generates_audio(self):
        resp = client.post(
            "/api/voice/tts",
            json={"text": "Hello world", "voice": "en-IN-NeerjaNeural"},
        )
        # edge-tts installed → 200 with audio/mpeg; not installed → 503
        assert resp.status_code in (200, 503)
        if resp.status_code == 200:
            assert resp.headers["content-type"] == "audio/mpeg"
            assert len(resp.content) > 0

    def test_tts_short_text_ok(self):
        resp = client.post("/api/voice/tts", json={"text": "Hi"})
        assert resp.status_code in (200, 503)

    def test_tts_custom_voice(self):
        resp = client.post(
            "/api/voice/tts",
            json={"text": "Test", "voice": "en-US-JennyNeural"},
        )
        assert resp.status_code in (200, 503)


class TestRouteExistence:
    """Verify all expected routes are registered."""

    def test_voice_sessions_route_exists(self):
        routes = [r.path for r in app.routes]
        assert "/api/voice/sessions" in routes

    def test_voice_message_route_exists(self):
        routes = [r.path for r in app.routes]
        assert "/api/voice/message" in routes

    def test_voice_tts_route_exists(self):
        routes = [r.path for r in app.routes]
        assert "/api/voice/tts" in routes

    def test_voice_session_messages_route_exists(self):
        routes = [r.path for r in app.routes]
        assert "/api/voice/sessions/{session_id}/messages" in routes

    def test_voice_session_delete_route_exists(self):
        routes = [r.path for r in app.routes]
        assert "/api/voice/sessions/{session_id}" in routes
