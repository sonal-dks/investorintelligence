"""Playwright-based scraper for Groww mutual fund pages."""

from __future__ import annotations

import asyncio
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from playwright.async_api import Page, async_playwright

from backend.config.settings import (
    DELAY_BETWEEN_PAGES_S,
    MAX_RETRIES_PER_URL,
    PAGE_TIMEOUT_MS,
    RETRY_BACKOFF_S,
    SCRAPER_CONCURRENCY,
)
from backend.models.schemas import ScrapeResult

logger = logging.getLogger(__name__)


def _slug_from_url(url: str) -> str:
    path = urlparse(url).path
    return path.rstrip("/").split("/")[-1]


def _parse_numeric(text: Optional[str]) -> Optional[float]:
    """Extract first numeric value from text, handling commas and ₹ symbols."""
    if not text:
        return None
    cleaned = text.replace(",", "").replace("₹", "").replace("%", "").strip()
    match = re.search(r"-?\d+\.?\d*", cleaned)
    if match:
        try:
            return float(match.group())
        except ValueError:
            return None
    return None


def _parse_int(text: Optional[str]) -> Optional[int]:
    val = _parse_numeric(text)
    return int(val) if val is not None else None


def _parse_date(text: Optional[str]) -> Optional[str]:
    """Try common date formats from Groww pages."""
    if not text:
        return None
    text = text.strip()
    for fmt in ("%d %b '%y", "%d %b %Y", "%d %b, %Y", "%b %d, %Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    date_match = re.search(r"(\d{1,2}\s+\w{3,9}\s+\d{4})", text)
    if date_match:
        for fmt in ("%d %b %Y", "%d %B %Y"):
            try:
                return datetime.strptime(date_match.group(1), fmt).strftime("%Y-%m-%d")
            except ValueError:
                continue
    return None


def _classify_category(text: Optional[str]) -> str:
    """Normalize fund category from page text."""
    if not text:
        return "Unknown"
    text_lower = text.lower().strip()
    categories = {
        "large cap": "Large Cap",
        "large & mid cap": "Large & Mid Cap",
        "mid cap": "Mid Cap",
        "small cap": "Small Cap",
        "flexi cap": "Flexi Cap",
        "multi cap": "Multicap",
        "multicap": "Multicap",
        "elss": "ELSS",
        "tax saver": "ELSS",
        "liquid": "Liquid",
        "debt": "Debt",
        "hybrid": "Hybrid",
        "aggressive hybrid": "Hybrid",
        "balanced advantage": "Hybrid",
        "equity savings": "Hybrid",
        "arbitrage": "Arbitrage",
        "sectoral": "Sectoral/Thematic",
        "thematic": "Sectoral/Thematic",
        "healthcare": "Sectoral/Thematic",
        "banking": "Sectoral/Thematic",
        "infrastructure": "Sectoral/Thematic",
        "consumption": "Sectoral/Thematic",
        "etf": "ETF/FOF",
        "fof": "ETF/FOF",
        "fund of fund": "ETF/FOF",
        "index": "Index",
        "dynamic bond": "Debt",
        "ultra short": "Debt",
        "multi asset": "Multi Asset",
        "focused": "Focused",
        "esg": "ESG",
    }
    for key, cat in categories.items():
        if key in text_lower:
            return cat
    return text.strip()


def _normalize_risk(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    text_lower = text.lower().strip()
    mapping = [
        ("very high", "Very High"),
        ("moderately high", "Moderately High"),
        ("low to moderate", "Moderate"),
        ("high", "High"),
        ("moderate", "Moderate"),
        ("low", "Low"),
    ]
    for key, val in mapping:
        if key in text_lower:
            return val
    return None


async def _extract_text(page: Page, selector: str) -> Optional[str]:
    """Safely extract text content from the first matching element."""
    try:
        el = page.locator(selector).first
        if await el.count() > 0:
            text = await el.text_content()
            return text.strip() if text else None
    except Exception:
        pass
    return None


async def _extract_returns(page: Page) -> dict[str, Optional[float]]:
    """Extract return percentages from the fund page returns section."""
    returns: dict[str, Optional[float]] = {
        "returns_1m": None,
        "returns_6m": None,
        "returns_1y": None,
        "returns_3y": None,
        "returns_5y": None,
    }
    try:
        # Groww typically shows returns in a table or structured section
        # Try multiple selector strategies
        selectors_to_try = [
            "[class*='return'] table",
            "[class*='Return'] table",
            "table",
        ]
        for table_sel in selectors_to_try:
            tables = page.locator(table_sel)
            count = await tables.count()
            if count > 0:
                text = await tables.first.text_content()
                if text and any(kw in text.lower() for kw in ["1y", "3y", "5y", "1 year", "3 year"]):
                    rows = text.strip().split("\n")
                    for row in rows:
                        row_lower = row.lower().strip()
                        val = _parse_numeric(row)
                        if val is not None:
                            if "1m" in row_lower or "1 month" in row_lower:
                                returns["returns_1m"] = val
                            elif "6m" in row_lower or "6 month" in row_lower:
                                returns["returns_6m"] = val
                            elif "1y" in row_lower or "1 year" in row_lower:
                                returns["returns_1y"] = val
                            elif "3y" in row_lower or "3 year" in row_lower:
                                returns["returns_3y"] = val
                            elif "5y" in row_lower or "5 year" in row_lower:
                                returns["returns_5y"] = val
                    if any(v is not None for v in returns.values()):
                        break

        # Fallback: look for individual return elements
        if all(v is None for v in returns.values()):
            all_text = await page.content()
            period_map = {
                "returns_1y": [r"1\s*(?:Y|year)[^\d]*(-?\d+\.?\d*)"],
                "returns_3y": [r"3\s*(?:Y|year)[^\d]*(-?\d+\.?\d*)"],
                "returns_5y": [r"5\s*(?:Y|year)[^\d]*(-?\d+\.?\d*)"],
            }
            for key, patterns in period_map.items():
                for pat in patterns:
                    m = re.search(pat, all_text, re.IGNORECASE)
                    if m:
                        returns[key] = float(m.group(1))
                        break

    except Exception as e:
        logger.debug("Returns extraction error: %s", e)

    return returns


def _parse_groww_body_text(body: str, html: str, fund_name: str) -> dict[str, Any | None]:
    """Extract key fields from Groww's 2025+ SPA layout (visible text + FAQ HTML)."""
    out: dict[str, Any | None] = {
        "nav_text": None,
        "nav_date_text": None,
        "category_text": None,
        "risk_text": None,
        "aum_text": None,
        "expense_text": None,
        "min_sip_text": None,
    }
    lines = [ln.strip() for ln in body.splitlines() if ln.strip()]

    # NAV block: "NAV: 06 May '26" then "₹125.22"
    for i, line in enumerate(lines):
        if line.upper().startswith("NAV:"):
            out["nav_date_text"] = line.split(":", 1)[1].strip()
            if i + 1 < len(lines) and "₹" in lines[i + 1]:
                out["nav_text"] = lines[i + 1]
            break

    # FAQ fallback: "The NAV of ... is ₹125.22 as of 06 May 2026."
    if not out["nav_text"]:
        m = re.search(
            r"The NAV of .+? is ₹([\d,]+\.?\d*)\s+as of\s+(\d{1,2}\s+\w+\s+\d{4})",
            html,
            re.IGNORECASE | re.DOTALL,
        )
        if m:
            out["nav_text"] = m.group(1)
            out["nav_date_text"] = m.group(2)

    # Category / risk: "Equity" → next line category → next line riskometer text
    for i, line in enumerate(lines[:40]):
        if line == "Equity" and i + 2 < len(lines):
            out["category_text"] = lines[i + 1]
            out["risk_text"] = lines[i + 2]
            break

    # Label → value (AUM, expense, min SIP)
    def _after(label: str) -> str | None:
        label_l = label.lower()
        for j, line in enumerate(lines):
            if label_l in line.lower() and j + 1 < len(lines):
                return lines[j + 1]
        return None

    out["aum_text"] = _after("Fund size") or _after("AUM")
    out["expense_text"] = _after("Expense ratio")
    out["min_sip_text"] = _after("Min. for SIP") or _after("Minimum")

    return out


async def _scrape_single_fund(page: Page, url: str) -> dict[str, Any]:
    """Scrape a single fund page and return raw data dict."""
    slug = _slug_from_url(url)
    start = time.monotonic()

    await page.goto(url, wait_until="domcontentloaded", timeout=PAGE_TIMEOUT_MS)
    # Wait for key content to render
    try:
        await page.wait_for_selector("h1", timeout=PAGE_TIMEOUT_MS)
    except Exception:
        logger.warning("h1 not found on %s, proceeding anyway", url)

    await page.wait_for_timeout(2500)

    fund_name = await _extract_text(page, "h1")
    body = await page.inner_text("body")
    html = await page.content()
    parsed = _parse_groww_body_text(body, html, fund_name or "")

    nav_text = parsed["nav_text"]
    nav_date_text = parsed["nav_date_text"]
    category_text = parsed["category_text"]
    aum_text = parsed["aum_text"]
    expense_text = parsed["expense_text"]
    min_sip_text = parsed["min_sip_text"]
    risk_text = parsed["risk_text"]

    # Legacy CSS fallbacks if body parse missed
    if not nav_text:
        nav_text = await _extract_text(page, "[class*='nav'] span, [class*='Nav'] span, [class*='NAV']")
    if not nav_date_text:
        nav_date_text = await _extract_text(page, "[class*='navDate'], [class*='nav-date'], [class*='NavDate']")
    if not category_text:
        category_text = await _extract_text(page, "[class*='category'], [class*='Category'], [class*='scheme']")
    if not aum_text:
        aum_text = await _extract_text(page, "[class*='aum'], [class*='AUM'], [class*='Aum']")
    if not expense_text:
        expense_text = await _extract_text(page, "[class*='expense'], [class*='Expense']")
    if not min_sip_text:
        min_sip_text = await _extract_text(page, "[class*='sip'], [class*='SIP'], [class*='minSip']")
    if not risk_text:
        risk_text = await _extract_text(page, "[class*='risk'], [class*='Risk'], [class*='riskometer']")

    exit_load_text = await _extract_text(page, "[class*='exitLoad'], [class*='exit-load'], [class*='ExitLoad']")
    tax_text = await _extract_text(page, "[class*='tax'], [class*='Tax']")

    returns = await _extract_returns(page)
    elapsed = time.monotonic() - start

    # Fallback: derive category from fund name if page extraction failed
    if not category_text and fund_name:
        category_text = fund_name

    # AUM on Groww is often "₹35,342.63 Cr" — store crores as numeric
    aum_cr = _parse_numeric(aum_text)

    data = {
        "fund_slug": slug,
        "fund_name": fund_name or slug.replace("-", " ").title(),
        "category": _classify_category(category_text),
        "nav": _parse_numeric(nav_text) or 0.0,
        "nav_date": _parse_date(nav_date_text),
        "aum_cr": aum_cr,
        "expense_ratio": _parse_numeric(expense_text),
        "min_sip": _parse_int(min_sip_text),
        "risk_level": _normalize_risk(risk_text),
        "exit_load_text": exit_load_text,
        "tax_text": tax_text,
        "source_url": url,
        "scraped_at": datetime.now(timezone.utc).isoformat(),
        **returns,
    }

    logger.info(
        "Scraped %s in %.1fs | NAV=%s | category=%s",
        slug, elapsed, data["nav"], data["category"],
    )
    return data


async def _scrape_with_retry(page: Page, url: str) -> dict[str, Any] | None:
    """Attempt scraping with retries and backoff."""
    for attempt in range(1, MAX_RETRIES_PER_URL + 1):
        try:
            return await _scrape_single_fund(page, url)
        except Exception as e:
            logger.warning(
                "Attempt %d/%d failed for %s: %s",
                attempt, MAX_RETRIES_PER_URL, url, e,
            )
            if attempt < MAX_RETRIES_PER_URL:
                await asyncio.sleep(RETRY_BACKOFF_S * attempt)
    return None


async def scrape_mutual_funds(urls: list[str]) -> ScrapeResult:
    """Scrape all fund URLs with concurrency control. Returns partial results on failures."""
    result = ScrapeResult()
    semaphore = asyncio.Semaphore(SCRAPER_CONCURRENCY)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)

        async def _worker(url: str) -> None:
            async with semaphore:
                context = await browser.new_context(
                    user_agent="InvestorOps-Scraper/1.0 (educational project)"
                )
                page = await context.new_page()
                try:
                    data = await _scrape_with_retry(page, url)
                    if data and data.get("nav", 0) > 0:
                        result.funds.append(data)
                    elif data:
                        result.errors.append({
                            "url": url,
                            "error": "NAV extraction failed (got 0 or None)",
                            "partial_data": data,
                        })
                    else:
                        result.errors.append({
                            "url": url,
                            "error": "All retry attempts exhausted",
                        })
                except Exception as e:
                    result.errors.append({"url": url, "error": str(e)})
                finally:
                    await context.close()
                    await asyncio.sleep(DELAY_BETWEEN_PAGES_S)

        tasks = [_worker(url) for url in urls]
        await asyncio.gather(*tasks, return_exceptions=True)
        await browser.close()

    logger.info(
        "Scraping complete: %d/%d succeeded, %d failed",
        len(result.funds), len(urls), len(result.errors),
    )
    return result
