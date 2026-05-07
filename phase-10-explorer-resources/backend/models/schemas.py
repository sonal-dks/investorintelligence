from __future__ import annotations

from pydantic import BaseModel


class Fund(BaseModel):
    fund_slug: str
    fund_name: str
    category: str | None = None
    nav: float | None = None
    nav_date: str | None = None
    aum_cr: float | None = None
    expense_ratio: float | None = None
    min_sip: int | None = None
    risk_level: str | None = None
    returns_1y: float | None = None
    returns_3y: float | None = None
    returns_5y: float | None = None
    source_url: str | None = None
    scraped_at: str | None = None


class FundsSummary(BaseModel):
    tracked_funds: int
    avg_expense_ratio: float
    high_risk_funds: int
    last_scraped_at: str | None = None


class FundsResponse(BaseModel):
    funds: list[Fund]
    summary: FundsSummary


class FeeItem(BaseModel):
    category: str
    description: str
    typical_range: str | None = None
    applicable_to: str | None = None
    notes: str | None = None


class FeeSection(BaseModel):
    fee_type: str
    title: str
    items: list[FeeItem]


class FeeExplainerResponse(BaseModel):
    sections: list[FeeSection]
    last_updated: str | None = None
    source_url: str | None = None
