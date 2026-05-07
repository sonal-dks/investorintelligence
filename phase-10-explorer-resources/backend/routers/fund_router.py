from __future__ import annotations

import httpx
from fastapi import APIRouter

from backend import config
from backend.models.schemas import FundsResponse, FundsSummary
from backend.services.fund_explorer_service import FundExplorerService

router = APIRouter(prefix="/api/funds", tags=["funds"])
_service = FundExplorerService()


def _sb_headers() -> dict[str, str]:
    key = config.supabase_service_role_key() or ""
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _sb_url(table: str) -> str:
    return f"{str(config.supabase_url()).rstrip('/')}/rest/v1/{table}"


def _load_fund_rows() -> list[dict] | None:
    if not config.supabase_enabled():
        return None
    try:
        r = httpx.get(
            _sb_url("mutual_fund_data"),
            params={"select": "*", "order": "scraped_at.desc", "limit": "5000"},
            headers=_sb_headers(),
            timeout=15.0,
        )
        r.raise_for_status()
        return r.json() or []
    except Exception:
        return None


def _funds_payload() -> dict:
    rows = _load_fund_rows()
    if rows is None:
        rows = _service.sample_rows()
    funds = _service.latest_funds(rows)
    summary = _service.build_summary(funds)
    return {"funds": funds, "summary": summary}


@router.get("", response_model=FundsResponse)
def get_funds() -> dict:
    return _funds_payload()


@router.get("/summary", response_model=FundsSummary)
def get_funds_summary() -> dict:
    return _funds_payload()["summary"]
