"""Request/response schemas for Phase 05 Smart Search."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


IntentType = Literal["factual", "action", "safety", "clarification"]
FactualCorpus = Literal["mutual_fund", "fee_explainer"]
MessageRole = Literal["user", "assistant", "system"]


class Citation(BaseModel):
    text: str
    source_url: str
    fund: str


class ChatMessageRequest(BaseModel):
    session_id: str
    content: str = Field(..., min_length=1, max_length=2000)


class ChatMessageResponse(BaseModel):
    id: str
    role: MessageRole
    content: str
    citations: list[Citation] = []
    metadata: dict = {}
    created_at: str


class ChatSessionCreate(BaseModel):
    pass


class ChatSession(BaseModel):
    id: str
    title: str
    last_message_at: str | None
    created_at: str


class ChatSessionListResponse(BaseModel):
    sessions: list[ChatSession]


class PIIScanResult(BaseModel):
    cleaned_text: str
    pii_found: bool
    findings: list[dict] = []


class RefusalResult(BaseModel):
    should_refuse: bool
    reason: str | None = None


class IntentClassification(BaseModel):
    intent_type: IntentType
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_tag: str = ""


class FactualCorpusClassification(BaseModel):
    """Sub-routing for factual RAG: mutual fund facts vs fee explainer corpus."""

    retrieval_corpus: FactualCorpus | None = None
    confidence: float = Field(ge=0.0, le=1.0)
    reasoning_tag: str = ""


class MemorySummary(BaseModel):
    user_id: str
    summary_text: str
    topics: list[str] = []
    updated_at: str
