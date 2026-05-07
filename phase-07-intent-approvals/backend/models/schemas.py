from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

IntentType = Literal['booking', 'email', 'calendar_hold', 'note', 'follow_up', 'cancel_booking', 'reschedule']
IntentStatus = Literal['detected', 'confirmed', 'cancelled', 'modified']
ApprovalStatus = Literal['pending', 'approved', 'rejected']
ActionType = Literal['calendar', 'email', 'booking', 'note', 'follow_up']


class ConversationMessage(BaseModel):
    role: Literal['user', 'assistant']
    content: str


class Intent(BaseModel):
    type: IntentType
    confidence: float = Field(..., ge=0.0, le=1.0)
    details: dict = Field(default_factory=dict)
    status: IntentStatus


class DetectIntentsRequest(BaseModel):
    session_id: str
    messages: list[ConversationMessage] = Field(default_factory=list, min_length=1)


class DetectIntentsResponse(BaseModel):
    intents: list[Intent]


class Approval(BaseModel):
    id: str
    action_type: ActionType
    title: str
    description: str = ''
    investor_id: str
    investor_name: str = 'Unknown Investor'
    status: ApprovalStatus = 'pending'
    priority: Literal['low', 'medium', 'high'] = 'medium'
    payload: dict
    source_session_id: str
    source_type: Literal['chat', 'voice'] = 'chat'
    reviewed_by: str | None = None
    reviewed_at: str | None = None
    created_at: str
    intent_hash: str


class ApprovalListResponse(BaseModel):
    items: list[Approval]
    total: int
    pending_count: int


class ApprovalStatsResponse(BaseModel):
    pending: int
    approved: int
    rejected: int
    total: int


class ApprovalPatchRequest(BaseModel):
    status: Literal['approved', 'rejected', 'pending']
    reviewed_by: str | None = None
