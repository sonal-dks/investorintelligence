"""TTSService — Edge TTS integration for server-side audio generation.

Uses the edge-tts library (unofficial Microsoft Edge TTS).
Falls back gracefully: if edge-tts is unavailable the endpoint returns 503
and the frontend uses browser SpeechSynthesis instead.
"""

from __future__ import annotations

import asyncio
import io
import logging

logger = logging.getLogger(__name__)

_edge_tts_available = True
try:
    import edge_tts
except ImportError:
    _edge_tts_available = False
    logger.warning("edge_tts_not_installed — TTS endpoint will return 503")


class TTSService:
    def __init__(self, default_voice: str = "en-IN-NeerjaNeural", max_text_length: int = 1000) -> None:
        self._default_voice = default_voice
        self._max_text_length = max_text_length

    @property
    def is_available(self) -> bool:
        return _edge_tts_available

    async def generate_audio(self, text: str, voice: str | None = None) -> bytes:
        if not _edge_tts_available:
            raise RuntimeError("edge-tts library not installed")

        text = text.strip()
        if not text:
            raise ValueError("Text must not be empty")
        if len(text) > self._max_text_length:
            text = text[: self._max_text_length]

        voice = voice or self._default_voice

        communicate = edge_tts.Communicate(text, voice)
        buffer = io.BytesIO()
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                buffer.write(chunk["data"])

        audio_bytes = buffer.getvalue()
        if not audio_bytes:
            raise RuntimeError("Edge TTS returned empty audio")

        logger.info("tts_generated", extra={"voice": voice, "text_len": len(text), "audio_bytes": len(audio_bytes)})
        return audio_bytes

    def generate_audio_sync(self, text: str, voice: str | None = None) -> bytes:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self.generate_audio(text, voice))
        finally:
            loop.close()
