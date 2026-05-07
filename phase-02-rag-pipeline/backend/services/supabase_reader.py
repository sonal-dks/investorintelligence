"""Supabase reader — pulls latest mutual_fund_data row per fund_slug.

The vector store is **derived** from Postgres (architecture.md "structured
source of truth + retrieval text layer"); this module is the only place we
read the canonical table.
"""

from __future__ import annotations

import logging
from typing import Iterable

from supabase import Client, create_client

from ..config.settings import SETTINGS

logger = logging.getLogger(__name__)


def get_client() -> Client:
    if not SETTINGS.supabase_url or not SETTINGS.supabase_service_role_key:
        raise RuntimeError(
            "Supabase credentials missing — set SUPABASE_URL and "
            "SUPABASE_SERVICE_ROLE_KEY in phase-02-rag-pipeline/.env"
        )
    return create_client(SETTINGS.supabase_url, SETTINGS.supabase_service_role_key)


def fetch_latest_funds(client: Client | None = None) -> list[dict]:
    """Return one row per fund_slug — the most recent scraped_at."""

    cli = client or get_client()
    response = (
        cli.table("mutual_fund_data")
        .select("*")
        .order("scraped_at", desc=True)
        .limit(5000)
        .execute()
    )
    rows: Iterable[dict] = response.data or []
    seen: set[str] = set()
    latest: list[dict] = []
    for row in rows:
        slug = row.get("fund_slug")
        if not slug or slug in seen:
            continue
        seen.add(slug)
        latest.append(row)
    logger.info("supabase_funds_fetched", extra={"count": len(latest)})
    return latest


def fetch_fee_explainer_rows(client: Client | None = None) -> list[dict]:
    """Load fee explainer rows for RAG narrative chunking (Phase 10 table)."""

    cli = client or get_client()
    try:
        response = (
            cli.table("fee_explainer_data")
            .select("*")
            .order("last_updated", desc=True)
            .limit(500)
            .execute()
        )
        rows = list(response.data or [])
        logger.info("supabase_fee_explainer_fetched", extra={"count": len(rows)})
        return rows
    except Exception as exc:  # noqa: BLE001 — table may be absent in early envs
        logger.warning("fee_explainer_fetch_failed", extra={"error": str(exc)})
        return []
