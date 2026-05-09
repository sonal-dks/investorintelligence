"""Pydantic schemas for scraped fund data and review data."""

from __future__ import annotations

from datetime import date, datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field, field_validator


VALID_RISK_LEVELS = {"Low", "Moderate", "Moderately High", "High", "Very High"}


class FundData(BaseModel):
    fund_slug: str
    fund_name: str
    category: str
    nav: float = Field(gt=0)
    nav_date: Optional[date] = None
    aum_cr: Optional[float] = Field(default=None, gt=0)
    expense_ratio: Optional[float] = Field(default=None, gt=0, lt=10)
    min_sip: Optional[int] = None
    min_lumpsum_first: Optional[int] = None
    min_lumpsum_second: Optional[int] = None
    risk_level: Optional[str] = None
    rating: Optional[int] = Field(default=None, ge=0, le=5)
    asset_class: Optional[str] = None
    lock_in_period: Optional[str] = None
    one_day_return_pct: Optional[float] = None
    returns_1m: Optional[float] = None
    returns_6m: Optional[float] = None
    returns_1y: Optional[float] = None
    returns_3y: Optional[float] = None
    returns_5y: Optional[float] = None
    returns_10y: Optional[float] = None
    returns_since_inception: Optional[float] = None
    exit_load_text: Optional[str] = None
    tax_text: Optional[str] = None
    stamp_duty_text: Optional[str] = None
    benchmark: Optional[str] = None
    investment_objective: Optional[str] = None
    fund_manager_name: Optional[str] = None
    fund_manager_tenure: Optional[str] = None
    return_calculator_sip: Optional[list[dict]] = None
    return_calculator_one_time: Optional[list[dict]] = None
    returns_and_rankings_annualised: Optional[dict] = None
    returns_and_rankings_absolute: Optional[dict] = None
    holding_analysis: Optional[dict] = None
    sector_allocation: Optional[list[dict]] = None
    advanced_ratios: Optional[dict] = None
    faq_items: Optional[list[dict[str, str]]] = None
    source_url: str
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("risk_level")
    @classmethod
    def validate_risk_level(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v not in VALID_RISK_LEVELS:
            raise ValueError(f"risk_level must be one of {VALID_RISK_LEVELS}, got '{v}'")
        return v

    @field_validator("fund_slug")
    @classmethod
    def validate_fund_slug(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("fund_slug cannot be empty")
        return v.strip()


class ReviewData(BaseModel):
    review_id: str
    reviewer_name: Optional[str] = None
    rating: int = Field(ge=1, le=5)
    review_text: Optional[str] = None
    review_date: Optional[date] = None
    thumbs_up: int = Field(default=0, ge=0)
    app_version: Optional[str] = None
    scraped_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    @field_validator("review_id")
    @classmethod
    def validate_review_id(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("review_id cannot be empty")
        return v.strip()


class ValidationError(BaseModel):
    index: int
    field: Optional[str] = None
    message: str
    raw_data: Optional[dict] = None


class ScrapeResult(BaseModel):
    funds: list[FundData] = Field(default_factory=list)
    errors: list[dict] = Field(default_factory=list)


class WriteResult(BaseModel):
    inserted: int = 0
    failed: int = 0
    errors: list[str] = Field(default_factory=list)
