"""Batch insert validated data to Supabase with error handling."""

from __future__ import annotations

import logging
from typing import Any

from supabase import create_client, Client

from backend.config.settings import BATCH_INSERT_SIZE, SUPABASE_SERVICE_ROLE_KEY, SUPABASE_URL
from backend.models.schemas import WriteResult

logger = logging.getLogger(__name__)


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
    records = _serialize(data)
    total = len(records)
    logger.info("Inserting %d records into %s (batch_size=%d)", total, table, BATCH_INSERT_SIZE)

    for i in range(0, total, BATCH_INSERT_SIZE):
        batch = records[i : i + BATCH_INSERT_SIZE]
        batch_num = (i // BATCH_INSERT_SIZE) + 1
        try:
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
