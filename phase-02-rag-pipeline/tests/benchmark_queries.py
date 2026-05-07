"""Hand-crafted benchmark queries for the precision exit-criterion.

Each entry: (query, expected_fund_slug_substring).  ``expected_fund_slug_substring``
keeps the test resilient to small fund-name variations across scrapes.

The benchmark is run by ``run_benchmark.py``.  Success criterion (architecture.md
Phase 02 §Success Criteria): top-3 precision > 80% on real Supabase corpus.

Queries are scoped to the 30-fund Mirae Asset universe configured in
``phase-01-data-ingestion/backend/config/settings.py`` and present in the
``mutual_fund_data`` table.
"""

from __future__ import annotations

BENCHMARK: list[tuple[str, str]] = [
    # 1) The mandatory architecture/PRD example
    ("What is the exit load of Mirae Asset Large Cap?", "mirae-asset-large-cap-fund"),
    # 2) Fact retrieval — NAV
    ("NAV of Mirae Asset Large Cap fund", "mirae-asset-large-cap-fund"),
    # 3) Fact retrieval — expense ratio
    ("expense ratio of Mirae Asset Flexi Cap", "mirae-asset-flexi-cap"),
    # 4) Fact retrieval — minimum SIP
    ("Minimum SIP for Mirae Asset ELSS Tax Saver", "mirae-asset-elss-tax-saver"),
    # 5) Risk level lookup
    ("Risk level of Mirae Asset Midcap", "mirae-asset-midcap-fund"),
    # 6) Exit load — different fund
    ("Exit load of Mirae Asset Small Cap Fund", "mirae-asset-small-cap"),
    # 7) AUM
    ("AUM of Mirae Asset Arbitrage Fund", "mirae-asset-arbitrage"),
    # 8) Returns
    ("Returns of Mirae Asset Healthcare Fund", "mirae-asset-healthcare"),
    # 9) Typo / shorthand (Addendum A2 mandatory)
    ("tell query about mirae larg cap exit load", "mirae-asset-large-cap-fund"),
    # 10) Casual phrasing
    ("NAV mirae arbitrage", "mirae-asset-arbitrage"),
    # 11) Reordered tokens
    ("ELSS tax saver Mirae expense", "mirae-asset-elss-tax-saver"),
    # 12) Long-form fund name
    ("Mirae Asset Banking and Financial Services Fund category", "mirae-asset-banking-and-financial-services"),
    # 13) Small Cap
    ("Mirae Asset Small Cap risk level", "mirae-asset-small-cap"),
    # 14) Liquid fund
    ("Mirae Asset Liquid fund expense ratio", "mirae-asset-liquid"),
    # 15) Hybrid fund
    ("Mirae Asset Aggressive Hybrid Fund NAV", "mirae-asset-aggressive-hybrid"),
    # 16) Large & Midcap
    ("Mirae Asset Large and Midcap minimum SIP", "mirae-asset-large-midcap"),
    # 17) Multicap
    ("Mirae Asset Multicap Fund AUM", "mirae-asset-multicap-fund"),
    # 18) Multi-asset
    ("Mirae Asset Multi Asset Allocation expense ratio", "mirae-asset-multi-asset-allocation"),
    # 19) Focused fund
    ("Mirae Asset Focused Fund risk", "mirae-asset-focused"),
    # 20) Sectoral
    ("Mirae Asset Great Consumer Fund returns", "mirae-asset-great-consumer"),
]
