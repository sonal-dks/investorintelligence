"""Google Play review scraper for the Groww app."""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone, timedelta
from typing import Any

from google_play_scraper import Sort, reviews

from backend.config.settings import (
    REVIEW_APP_ID,
    REVIEW_COUNT,
    REVIEW_LANGUAGE,
    REVIEW_LOOKBACK_DAYS,
)

logger = logging.getLogger(__name__)

_PROFANITY = {
    "fuck", "fucking", "shit", "bitch", "asshole", "bastard", "motherfucker",
    "madarchod", "bhosdike", "chutiya", "bc", "mc",
}


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w']+\b", text))


def _is_english_like(text: str) -> bool:
    # Lightweight heuristic: mostly latin letters and at least one common English token.
    letters = re.findall(r"[A-Za-z]", text)
    if len(letters) < 10:
        return False
    non_latin = re.findall(r"[^\x00-\x7F]", text)
    if non_latin and (len(non_latin) / max(len(text), 1)) > 0.15:
        return False
    lower = text.lower()
    common = ("the", "and", "app", "is", "to", "for", "very", "good", "bad", "not")
    return any(f" {w} " in f" {lower} " for w in common)


def _contains_profanity(text: str) -> bool:
    lower = text.lower()
    return any(re.search(rf"\b{re.escape(word)}\b", lower) for word in _PROFANITY)


def _is_clean_review_text(text: str | None) -> bool:
    if not text:
        return False
    if _word_count(text) < 5:
        return False
    if not _is_english_like(text):
        return False
    if _contains_profanity(text):
        return False
    return True


def scrape_reviews(
    app_id: str = REVIEW_APP_ID,
    count: int = REVIEW_COUNT,
    language: str = REVIEW_LANGUAGE,
    lookback_days: int = REVIEW_LOOKBACK_DAYS,
) -> list[dict[str, Any]]:
    """Fetch latest reviews from Google Play, sorted by newest.

    Returns list of raw review dicts mapped to our schema.
    Deduplicates by review_id.
    """
    logger.info(
        "Fetching reviews for app=%s lang=%s lookback_days=%d initial_count=%d",
        app_id,
        language,
        lookback_days,
        count,
    )

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
        result: list[dict[str, Any]] = []
        continuation = None
        # Paginate until we hit lookback boundary or no more pages.
        while True:
            batch, continuation = reviews(
                app_id,
                lang=language,
                country="in",
                sort=Sort.NEWEST,
                count=count,
                continuation_token=continuation,
            )
            if not batch:
                break
            result.extend(batch)
            oldest = batch[-1].get("at")
            if isinstance(oldest, datetime):
                oldest_utc = oldest.replace(tzinfo=timezone.utc) if oldest.tzinfo is None else oldest.astimezone(timezone.utc)
                if oldest_utc < cutoff:
                    break
            if not continuation:
                break
    except Exception as e:
        logger.error("Google Play scraper failed: %s", e)
        return []

    seen_ids: set[str] = set()
    mapped: list[dict[str, Any]] = []
    cutoff = datetime.now(timezone.utc) - timedelta(days=lookback_days)
    dropped_old = 0
    dropped_dirty = 0

    for r in result:
        review_id = r.get("reviewId", "")
        if not review_id or review_id in seen_ids:
            continue
        seen_ids.add(review_id)

        review_date = r.get("at")
        review_dt_utc = None
        if isinstance(review_date, datetime):
            review_dt_utc = review_date.replace(tzinfo=timezone.utc) if review_date.tzinfo is None else review_date.astimezone(timezone.utc)
            if review_dt_utc < cutoff:
                dropped_old += 1
                continue
        text = r.get("content")
        if not _is_clean_review_text(text):
            dropped_dirty += 1
            continue

        if isinstance(review_date, datetime):
            review_date = review_date.strftime("%Y-%m-%d")
        elif review_date is not None:
            review_date = str(review_date)

        mapped.append({
            "review_id": review_id,
            "reviewer_name": r.get("userName"),
            "rating": r.get("score", 0),
            "review_text": text,
            "review_date": review_date,
            "thumbs_up": r.get("thumbsUpCount", 0),
            "app_version": r.get("reviewCreatedVersion"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    logger.info(
        "Fetched %d cleaned reviews (from %d raw, dropped_old=%d, dropped_dirty=%d)",
        len(mapped),
        len(result),
        dropped_old,
        dropped_dirty,
    )
    return mapped
