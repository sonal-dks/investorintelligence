"""Main orchestrator: scrape funds + reviews → validate → write to Supabase.

Usage:
    python run_scraper.py                    # full run (30 URLs + reviews)
    python run_scraper.py --urls 3           # scrape first 3 URLs only (testing)
    python run_scraper.py --skip-reviews     # skip Google Play reviews
    python run_scraper.py --skip-funds       # skip mutual-fund scrape
    python run_scraper.py --dry-run          # validate only, skip Supabase writes
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path

from backend.config.settings import FUND_URLS
from backend.scrapers.mutual_fund_scraper import scrape_mutual_funds
from backend.scrapers.review_scraper import scrape_reviews
from backend.validators.data_validator import validate_funds, validate_reviews
from backend.db.supabase_writer import write_to_supabase

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("run_scraper")


def _print_summary(section: str, total: int, valid: int, errors: int) -> None:
    logger.info("=== %s Summary ===", section)
    logger.info("  Total attempted: %d", total)
    logger.info("  Valid:           %d", valid)
    logger.info("  Errors:          %d", errors)


async def main(args: argparse.Namespace) -> int:
    start = time.monotonic()
    exit_code = 0

    urls = [] if args.skip_funds else (FUND_URLS[: args.urls] if args.urls else FUND_URLS)
    logger.info("Starting scrape: %d fund URLs, reviews=%s, dry_run=%s",
                len(urls), not args.skip_reviews, args.dry_run)

    # --- Scrape mutual funds ---
    fund_scrape_errors: list[dict] = []
    fund_rows: list[dict] = []
    valid_funds = []
    fund_errors = []
    if not args.skip_funds:
        logger.info("--- Phase: Mutual Fund Scraping ---")
        fund_result = await scrape_mutual_funds(urls)
        fund_rows = fund_result.funds
        fund_scrape_errors = fund_result.errors
        valid_funds, fund_errors = validate_funds(fund_rows)
        _print_summary(
            "Mutual Funds",
            total=len(urls),
            valid=len(valid_funds),
            errors=len(fund_scrape_errors) + len(fund_errors),
        )

        if fund_errors:
            for err in fund_errors[:10]:
                logger.warning("  Validation error: index=%d field=%s msg=%s",
                               err.index, err.field, err.message)

        if fund_scrape_errors:
            for err in fund_scrape_errors[:10]:
                logger.warning("  Scrape error: url=%s error=%s", err.get("url"), err.get("error"))
    else:
        logger.info("--- Skipping mutual fund scraping ---")

    # --- Scrape reviews ---
    valid_reviews = []
    review_errors = []
    if not args.skip_reviews:
        logger.info("--- Phase: Review Scraping ---")
        raw_reviews = scrape_reviews()
        valid_reviews, review_errors = validate_reviews(raw_reviews)
        _print_summary(
            "App Reviews",
            total=len(raw_reviews),
            valid=len(valid_reviews),
            errors=len(review_errors),
        )
    else:
        logger.info("--- Skipping review scraping ---")

    # --- Persist raw JSON snapshots before any DB write ---
    snapshot_dir = Path(__file__).resolve().parent / "expected_outputs" / "actual_output"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    funds_payload = [f.model_dump(mode="json") for f in valid_funds]
    reviews_payload = [r.model_dump(mode="json") for r in valid_reviews]
    (snapshot_dir / "funds_latest.json").write_text(
        json.dumps(funds_payload, indent=2, default=str),
        encoding="utf-8",
    )
    (snapshot_dir / "reviews_latest.json").write_text(
        json.dumps(reviews_payload, indent=2, default=str),
        encoding="utf-8",
    )
    logger.info(
        "Saved local JSON snapshots before Supabase write: %s",
        snapshot_dir,
    )

    # --- Write to Supabase ---
    fund_write = None
    review_write = None
    if not args.dry_run:
        logger.info("--- Phase: Supabase Write ---")
        if valid_funds:
            fund_write = await write_to_supabase(valid_funds, "mutual_fund_data")
            logger.info("Funds: inserted=%d failed=%d", fund_write.inserted, fund_write.failed)
            if fund_write.failed > 0:
                exit_code = 1

        if valid_reviews:
            review_write = await write_to_supabase(valid_reviews, "app_reviews")
            logger.info("Reviews: inserted=%d failed=%d", review_write.inserted, review_write.failed)
            if review_write.failed > 0:
                exit_code = 1
    else:
        logger.info("--- Dry run: skipping Supabase writes ---")

    if args.refresh_rag and not args.dry_run:
        logger.info("--- Phase: RAG index refresh (phase-02) ---")
        try:
            phase02 = Path(__file__).resolve().parent.parent / "phase-02-rag-pipeline"
            if str(phase02) not in sys.path:
                sys.path.insert(0, str(phase02))
            from backend.services.rag_pipeline import RAGPipeline

            rag = RAGPipeline()
            res = rag.refresh()
            logger.info(
                "RAG refresh: status=%s chunks=%d collection_size=%d",
                res.status,
                res.chunks_generated,
                res.collection_size,
            )
            if res.status != "success":
                exit_code = 1
        except Exception:
            logger.exception("rag_refresh_failed")
            exit_code = 1

    if args.export_json:
        out_dir = Path(args.export_json)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "funds.json").write_text(json.dumps(funds_payload, indent=2, default=str), encoding="utf-8")
        (out_dir / "reviews.json").write_text(json.dumps(reviews_payload, indent=2, default=str), encoding="utf-8")
        logger.info("Exported %d funds, %d reviews to %s", len(funds_payload), len(reviews_payload), out_dir)

    # --- Final summary ---
    elapsed = time.monotonic() - start
    summary = {
        "elapsed_seconds": round(elapsed, 1),
        "funds_attempted": len(urls),
        "funds_scraped": len(fund_rows),
        "funds_valid": len(valid_funds),
        "funds_validation_errors": len(fund_errors),
        "funds_scrape_errors": len(fund_scrape_errors),
        "funds_inserted": fund_write.inserted if fund_write else 0,
        "reviews_fetched": len(valid_reviews),
        "reviews_validation_errors": len(review_errors),
        "reviews_inserted": review_write.inserted if review_write else 0,
    }
    logger.info("=== FINAL SUMMARY ===")
    logger.info(json.dumps(summary, indent=2))

    # Fail if fewer than 50% of URLs succeeded
    if (not args.skip_funds) and len(valid_funds) < len(urls) * 0.5:
        logger.error("CRITICAL: fewer than 50%% of URLs scraped successfully")
        exit_code = 1

    return exit_code


def cli() -> None:
    parser = argparse.ArgumentParser(description="Mutual Fund & Review Scraper")
    parser.add_argument("--urls", type=int, default=0, help="Limit to first N URLs (0=all)")
    parser.add_argument("--skip-funds", action="store_true", help="Skip mutual fund scraping")
    parser.add_argument("--skip-reviews", action="store_true", help="Skip Google Play reviews")
    parser.add_argument("--dry-run", action="store_true", help="Validate only, skip writes")
    parser.add_argument(
        "--export-json",
        metavar="DIR",
        help="After scrape/validation, write funds.json and reviews.json (for MCP SQL insert)",
    )
    parser.add_argument(
        "--refresh-rag",
        action="store_true",
        help="After successful Supabase writes, rebuild Phase 02 Chroma index (MF + fee explainer)",
    )
    args = parser.parse_args()
    if args.skip_funds and args.skip_reviews:
        parser.error("Cannot set both --skip-funds and --skip-reviews in the same run.")
    code = asyncio.run(main(args))
    sys.exit(code)


if __name__ == "__main__":
    cli()
