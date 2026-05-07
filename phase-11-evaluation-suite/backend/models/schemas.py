from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

CaseType = Literal["rag_faithfulness", "rag_relevance", "safety", "ux"]
RunType = Literal["scheduled", "manual"]


class EvalRunRequest(BaseModel):
    run_type: RunType = "manual"


class EvalCaseResult(BaseModel):
    id: str
    case_type: CaseType
    query: str
    expected_behavior: str
    actual_output: str
    passed: bool
    judge_reasoning: str = ""
    created_at: datetime


class EvalRunResult(BaseModel):
    run_id: str
    status: Literal["completed", "in_progress", "failed"] = "completed"
    run_type: RunType
    rag_faithfulness_pct: float = Field(ge=0, le=100)
    rag_relevance_pct: float = Field(ge=0, le=100)
    safety_pass_pct: float = Field(ge=0, le=100)
    pulse_word_count: int = 0
    action_items_count: int = 0
    total_cases: int = 0
    passed_cases: int = 0
    started_at: datetime
    completed_at: datetime | None = None


class EvalRunWithCases(BaseModel):
    run: EvalRunResult
    cases: list[EvalCaseResult]
