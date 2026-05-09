from __future__ import annotations

from backend.services.fund_explorer_service import FundExplorerService


def test_latest_fund_selection_and_missing_fields():
    svc = FundExplorerService()
    rows = [
        {"fund_slug": "a", "fund_name": "A", "scraped_at": "2026-05-01T00:00:00Z", "returns_5y": 12.0},
        {"fund_slug": "a", "fund_name": "A", "scraped_at": "2026-05-03T00:00:00Z", "returns_5y": None},
        {"fund_slug": "b", "fund_name": "B", "scraped_at": "2026-05-02T00:00:00Z", "returns_5y": 8.0},
    ]
    funds = svc.latest_funds(rows)
    assert len(funds) == 2
    assert next(f for f in funds if f["fund_slug"] == "a")["returns_5y"] is None


def test_summary_calculation():
    svc = FundExplorerService()
    funds = [
        {"expense_ratio": 0.5, "risk_level": "High", "scraped_at": "2026-05-03T00:00:00Z"},
        {"expense_ratio": 0.7, "risk_level": "Moderate", "scraped_at": "2026-05-01T00:00:00Z"},
    ]
    summary = svc.build_summary(funds)
    assert summary["tracked_funds"] == 2
    assert summary["avg_expense_ratio"] == 0.6
    assert summary["high_risk_funds"] == 1
