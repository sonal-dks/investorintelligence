from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Sentiment = Literal["positive", "neutral", "negative"]


class Review(BaseModel):
    reviewer_name: str
    rating: int = Field(ge=1, le=5)
    review_text: str
    review_date: str
    sentiment: Sentiment | None = None


class PulseLatestResponse(BaseModel):
    week_start: str
    overall_rating: float
    total_reviews: int
    positive_count: int
    neutral_count: int
    negative_count: int
    summary_text: str
    action_items: list[str]
    themes: list[dict]
    llm_themes: list[dict] = []
    deterministic_themes: list[dict] = []
    top_themes: list[dict] = Field(default_factory=list)
    user_quotes: list[str] = Field(default_factory=list)
    llm_summary_text: str | None = None
    deterministic_summary_text: str | None = None
    model_path: str | None = None
    model_used: str | None = None
    deterministic_algorithm: str | None = None
    judge_overall_score: float = 0.0
    judge_metrics: dict = Field(default_factory=dict)
    judge_rationale: str | None = None
    generated_at: str


class PulseReviewsResponse(BaseModel):
    reviews: list[Review]
    total: int
    page: int


class PulseKeywordsResponse(BaseModel):
    keywords: list[dict]


class PulseTrendsResponse(BaseModel):
    trends: list[dict]
