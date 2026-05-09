"""Batch insert validated data to Supabase with error handling."""

from __future__ import annotations

import logging
from typing import Any

from supabase import create_client, Client

from backend.config.settings import BATCH_INSERT_SIZE, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from backend.models.schemas import WriteResult

logger = logging.getLogger(__name__)

_MUTUAL_FUND_DB_COLUMNS = {
    "fund_slug",
    "fund_name",
    "category",
    "nav",
    "nav_date",
    "aum_cr",
    "expense_ratio",
    "min_sip",
    "min_lumpsum_first",
    "min_lumpsum_second",
    "risk_level",
    "rating",
    "asset_class",
    "lock_in_period",
    "one_day_return_pct",
    "returns_1m",
    "returns_6m",
    "returns_1y",
    "returns_3y",
    "returns_5y",
    "returns_10y",
    "returns_since_inception",
    "exit_load_text",
    "tax_text",
    "stamp_duty_text",
    "benchmark",
    "investment_objective",
    "fund_manager_name",
    "fund_manager_tenure",
    "return_calculator_sip",
    "return_calculator_one_time",
    "returns_and_rankings_annualised",
    "returns_and_rankings_absolute",
    "holding_analysis",
    "sector_allocation",
    "advanced_ratios",
    "faq_items",
    "source_url",
    "scraped_at",
}


def _get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set. "
            "Check your .env file or environment variables."
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _serialize(records: list[Any]) -> list[dict[str, Any]]:
    """Convert Pydantic models to dicts, handling date/datetime serialization."""
    out: list[dict[str, Any]] = []
    for rec in records:
        d = rec.model_dump() if hasattr(rec, "model_dump") else dict(rec)
        for k, v in d.items():
            if hasattr(v, "isoformat"):
                d[k] = v.isoformat()
        out.append(d)
    return out


def _filter_table_columns(records: list[dict[str, Any]], table: str) -> list[dict[str, Any]]:
    if table != "mutual_fund_data":
        return records
    filtered: list[dict[str, Any]] = []
    for row in records:
        filtered.append({k: v for k, v in row.items() if k in _MUTUAL_FUND_DB_COLUMNS})
    return filtered


async def write_to_supabase(
    data: list[Any],
    table: str,
) -> WriteResult:
    """Batch insert records to Supabase table.

    Inserts in chunks of BATCH_INSERT_SIZE.
    On per-batch failure: logs error, continues with remaining batches.
    """
    result = WriteResult()
    if not data:
        logger.info("No data to insert into %s", table)
        return result

    client = _get_client()
    records = _filter_table_columns(_serialize(data), table)
    total = len(records)
    logger.info("Inserting %d records into %s (batch_size=%d)", total, table, BATCH_INSERT_SIZE)

    for i in range(0, total, BATCH_INSERT_SIZE):
        batch = records[i : i + BATCH_INSERT_SIZE]
        batch_num = (i // BATCH_INSERT_SIZE) + 1
        try:
            if table == "app_reviews":
                # Reruns over rolling windows are expected; ignore duplicate review_id rows.
                response = (
                    client.table(table)
                    .upsert(batch, on_conflict="review_id", ignore_duplicates=True)
                    .execute()
                )
            else:
                response = client.table(table).insert(batch).execute()
            inserted = len(response.data) if response.data else len(batch)
            result.inserted += inserted
            logger.info("Batch %d: inserted %d rows into %s", batch_num, inserted, table)
        except Exception as e:
            result.failed += len(batch)
            error_msg = f"Batch {batch_num} failed for {table}: {e}"
            result.errors.append(error_msg)
            logger.error(error_msg)

    logger.info(
        "Write complete for %s: %d inserted, %d failed",
        table, result.inserted, result.failed,
    )
    return result
