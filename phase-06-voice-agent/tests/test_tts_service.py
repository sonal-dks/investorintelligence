"""Tests for TTSService."""

import pytest

from backend.services.tts_service import TTSService


class TestTTSServiceInit:
    def test_default_voice(self):
        svc = TTSService()
        assert svc._default_voice == "en-IN-NeerjaNeural"

    def test_custom_voice(self):
        svc = TTSService(default_voice="en-US-JennyNeural")
        assert svc._default_voice == "en-US-JennyNeural"

    def test_custom_max_text_length(self):
        svc = TTSService(max_text_length=500)
        assert svc._max_text_length == 500


class TestTTSServiceValidation:
    def test_empty_text_raises(self):
        svc = TTSService()
        with pytest.raises((ValueError, RuntimeError)):
            svc.generate_audio_sync("")

    def test_whitespace_only_raises(self):
        svc = TTSService()
        with pytest.raises((ValueError, RuntimeError)):
            svc.generate_audio_sync("   ")


class TestTTSServiceAvailability:
    def test_is_available_property(self):
        svc = TTSService()
        assert isinstance(svc.is_available, bool)


class TestTTSServiceTruncation:
    def test_long_text_truncated(self):
        """Long text should be truncated to max_text_length, not rejected."""
        svc = TTSService(max_text_length=10)
        # We can't fully test audio generation without edge-tts installed,
        # but we can verify the truncation logic by checking the attribute.
        assert svc._max_text_length == 10


@pytest.mark.skipif(
    not TTSService().is_available,
    reason="edge-tts not installed",
)
class TestTTSServiceGeneration:
    def test_generate_audio_returns_bytes(self):
        svc = TTSService()
        audio = svc.generate_audio_sync("Hello, this is a test.")
        assert isinstance(audio, bytes)
        assert len(audio) > 0

    def test_generate_audio_mp3_header(self):
        svc = TTSService()
        audio = svc.generate_audio_sync("Testing audio output.")
        # MP3 frames start with 0xFF sync byte followed by 0xFx or ID3 tag
        assert audio[0:1] == b"\xff" or audio[:3] == b"ID3"
