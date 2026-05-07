"""Tests for Phase 06 Pydantic schemas."""

import pytest
from pydantic import ValidationError

from backend.models.schemas import (
    TTSRequest,
    VoiceMessageRequest,
    VoiceMessageResponse,
    VoiceSession,
)


class TestVoiceMessageRequest:
    def test_valid_request(self):
        req = VoiceMessageRequest(session_id="abc", content="Hello", input_mode="voice")
        assert req.input_mode == "voice"

    def test_default_input_mode_is_text(self):
        req = VoiceMessageRequest(session_id="abc", content="Hello")
        assert req.input_mode == "text"

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            VoiceMessageRequest(session_id="abc", content="")

    def test_too_long_content_rejected(self):
        with pytest.raises(ValidationError):
            VoiceMessageRequest(session_id="abc", content="x" * 2001)

    def test_invalid_input_mode_rejected(self):
        with pytest.raises(ValidationError):
            VoiceMessageRequest(session_id="abc", content="Hi", input_mode="audio")


class TestTTSRequest:
    def test_valid_request(self):
        req = TTSRequest(text="Hello world")
        assert req.voice == "en-IN-NeerjaNeural"

    def test_empty_text_rejected(self):
        with pytest.raises(ValidationError):
            TTSRequest(text="")

    def test_too_long_text_rejected(self):
        with pytest.raises(ValidationError):
            TTSRequest(text="x" * 1001)

    def test_custom_voice(self):
        req = TTSRequest(text="Hello", voice="en-US-JennyNeural")
        assert req.voice == "en-US-JennyNeural"


class TestVoiceSession:
    def test_valid_session(self):
        s = VoiceSession(id="1", title="Test", mode="voice", last_message_at=None, created_at="2026-01-01")
        assert s.mode == "voice"


class TestVoiceMessageResponse:
    def test_voice_hint_default(self):
        r = VoiceMessageResponse(id="1", role="assistant", content="Hi", created_at="2026-01-01")
        assert r.voice_hint == "concise"
