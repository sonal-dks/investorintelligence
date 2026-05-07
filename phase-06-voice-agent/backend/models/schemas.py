"""Request/response schemas for Phase 06 Voice Agent."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

InputMode = Literal["voice", "text"]
MessageRole = Literal["user", "assistant"]
SessionMode = Literal["voice", "text"]


class Citation(BaseModel):
    text: str
    source_url: str
    fund: str


class VoiceMessageRequest(BaseModel):
    session_id: str
    content: str = Field(..., min_length=1, max_length=2000)
    input_mode: InputMode = "text"


class VoiceMessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    citations: list[Citation] = []
    metadata: dict = {}
    voice_hint: str = "concise"
    created_at: str


class TTSRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)
    voice: str = "en-IN-NeerjaNeural"


class VoiceSession(BaseModel):
    id: str
    title: str
    mode: SessionMode
    last_message_at: str | None
    created_at: str


class VoiceSessionListResponse(BaseModel):
    sessions: list[VoiceSession]


class VoiceGreetingThemeResponse(BaseModel):
    greeting: str
    top_theme: str | None = None
