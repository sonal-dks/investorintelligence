"""Phase 01 configuration: fund URLs, scraper settings, and env vars."""

import os
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

SCRAPER_CONCURRENCY = 5
PAGE_TIMEOUT_MS = 15_000
DELAY_BETWEEN_PAGES_S = 2.0
MAX_RETRIES_PER_URL = 3
RETRY_BACKOFF_S = 5.0
BATCH_INSERT_SIZE = 50

REVIEW_APP_ID = "com.nextbillion.groww"
REVIEW_COUNT = 100
REVIEW_LANGUAGE = "en"

FUND_URLS: list[str] = [
    "https://groww.in/mutual-funds/mirae-asset-elss-tax-saver-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-large-midcap-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-midcap-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-bse-india-defence-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-gold-silver-passive-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-nifty-metal-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-nifty-smallcap-250-momentum-quality-100-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-multicap-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-healthcare-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-liquid-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-flexi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-great-consumer-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-nifty-midsmallcap400-momentum-quality-100-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-banking-and-financial-services-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-gold-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-multi-asset-allocation-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-aggressive-hybrid-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-infrastructure-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-nifty-india-new-age-consumption-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-ultra-short-duration-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-silver-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-equity-savings-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-diversified-equity-allocator-passive-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-arbitrage-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-dynamic-bond-fund-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-nifty-100-esg-sector-leaders-fof-direct-growth",
    "https://groww.in/mutual-funds/mirae-asset-balanced-advantage-fund-direct-growth",
]

# CSS selectors for Groww fund page data extraction (configurable, not hardcoded)
SELECTORS: dict[str, str] = {
    "fund_name": "h1",
    "nav": "[data-test-id='fundNAV'], .nav__value, .fundNAV span",
    "nav_date": ".nav-date, .navDate, [class*='navDate']",
    "category": "[data-test-id='fundCategory'], .category, .schemeCategory",
    "aum": "[data-test-id='fundAUM'], .aum, [class*='aum']",
    "expense_ratio": "[data-test-id='expenseRatio'], .expenseRatio",
    "min_sip": "[data-test-id='minSIP'], .minSip",
    "risk_level": "[data-test-id='riskLevel'], .riskLevel, .riskometer",
    "exit_load": "[data-test-id='exitLoad'], .exitLoad",
    "returns_table": "table.returnsTable, [class*='returnsTable'], [class*='return']",
}
