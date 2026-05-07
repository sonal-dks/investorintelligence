"""Google Play review scraper for the Groww app."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from google_play_scraper import Sort, reviews

from backend.config.settings import REVIEW_APP_ID, REVIEW_COUNT, REVIEW_LANGUAGE

logger = logging.getLogger(__name__)


def scrape_reviews(
    app_id: str = REVIEW_APP_ID,
    count: int = REVIEW_COUNT,
    language: str = REVIEW_LANGUAGE,
) -> list[dict[str, Any]]:
    """Fetch latest reviews from Google Play, sorted by newest.

    Returns list of raw review dicts mapped to our schema.
    Deduplicates by review_id.
    """
    logger.info("Fetching %d reviews for app=%s lang=%s", count, app_id, language)

    try:
        result, _continuation = reviews(
            app_id,
            lang=language,
            country="in",
            sort=Sort.NEWEST,
            count=count,
        )
    except Exception as e:
        logger.error("Google Play scraper failed: %s", e)
        return []

    seen_ids: set[str] = set()
    mapped: list[dict[str, Any]] = []

    for r in result:
        review_id = r.get("reviewId", "")
        if not review_id or review_id in seen_ids:
            continue
        seen_ids.add(review_id)

        review_date = r.get("at")
        if isinstance(review_date, datetime):
            review_date = review_date.strftime("%Y-%m-%d")
        elif review_date is not None:
            review_date = str(review_date)

        mapped.append({
            "review_id": review_id,
            "reviewer_name": r.get("userName"),
            "rating": r.get("score", 0),
            "review_text": r.get("content"),
            "review_date": review_date,
            "thumbs_up": r.get("thumbsUpCount", 0),
            "app_version": r.get("reviewCreatedVersion"),
            "scraped_at": datetime.now(timezone.utc).isoformat(),
        })

    logger.info("Fetched %d unique reviews (from %d raw)", len(mapped), len(result))
    return mapped
