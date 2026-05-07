"""Shared pytest fixtures for phase-02 tests.

Adds the phase-02 root to sys.path so ``backend.*`` imports work the same way
they do at runtime, without any package install.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture(scope="session")
def sample_fund() -> dict:
    """A complete fund row that mirrors the Supabase ``mutual_fund_data`` shape."""

    return {
        "fund_slug": "mirae-asset-large-cap-fund-direct-growth",
        "fund_name": "Mirae Asset Large Cap Fund Direct Growth",
        "category": "Large Cap",
        "nav": 105.43,
        "nav_date": "2026-05-06",
        "aum_cr": 43215.67,
        "expense_ratio": 0.53,
        "min_sip": 500,
        "risk_level": "Very High",
        "returns_1y": 14.5,
        "returns_3y": 18.2,
        "returns_5y": 16.7,
        "exit_load_text": (
            "Understand termsExit loadA fee payable to a mutual fund house. "
            "Exit Load 05 Jan 2017 Exit load of 1% if redeemed within 1 year. "
            "01 Jan 2013 Exit load of 2% if redeemed within 6 months."
        ),
        "tax_text": "LTCG 12.5% above ₹1.25L after 1 year; STCG 20% within 1 year.",
        "source_url": "https://groww.in/mutual-funds/mirae-asset-large-cap-fund-direct-growth",
        "scraped_at": "2026-05-07T00:00:00Z",
    }


@pytest.fixture(scope="session")
def sparse_fund() -> dict:
    """Fund with most fields missing (new launch scenario)."""

    return {
        "fund_slug": "new-launch-fund-direct-growth",
        "fund_name": "New Launch Fund Direct Growth",
        "category": "Flexi Cap",
        "nav": 10.0,
        "source_url": "https://groww.in/mutual-funds/new-launch-fund-direct-growth",
        "scraped_at": "2026-05-07T00:00:00Z",
    }


@pytest.fixture(scope="session")
def malformed_fund() -> dict:
    """Fund missing required fields — chunker must skip it."""

    return {
        "fund_slug": "",
        "fund_name": None,
        "category": None,
        "nav": 12.34,
    }
