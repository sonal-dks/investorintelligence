from __future__ import annotations

import httpx
from fastapi import APIRouter, HTTPException

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


def _supabase_config_error() -> str | None:
    if not config.supabase_url():
        return "SUPABASE_URL is missing"
    if not config.supabase_service_role_key():
        return "SUPABASE_SERVICE_ROLE_KEY is missing"
    if not config.supabase_enabled():
        return "Supabase access disabled by PHASE10_DISABLE_SUPABASE"
    return None


def _load_fund_rows() -> list[dict]:
    cfg_error = _supabase_config_error()
    if cfg_error:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "supabase_not_configured",
                "message": "Phase 10 requires live Supabase data. Sample fallback is disabled.",
                "reason": cfg_error,
            },
        )

    if not config.supabase_enabled():
        raise HTTPException(
            status_code=503,
            detail={
                "code": "supabase_not_enabled",
                "message": "Phase 10 requires live Supabase data. Sample fallback is disabled.",
            },
        )
    try:
        r = httpx.get(
            _sb_url("mutual_fund_data"),
            params={"select": "*", "order": "scraped_at.desc", "limit": "5000"},
            headers=_sb_headers(),
            timeout=15.0,
        )
        r.raise_for_status()
        return r.json() or []
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "supabase_query_failed",
                "message": "Supabase query for mutual_fund_data failed.",
                "upstream_status": exc.response.status_code,
                "upstream_body": exc.response.text[:300],
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "supabase_request_error",
                "message": "Supabase request for mutual_fund_data failed before response.",
                "error": str(exc),
            },
        ) from exc


def _funds_payload() -> dict:
    rows = _load_fund_rows()
    funds = _service.latest_funds(rows)
    summary = _service.build_summary(funds)
    return {"funds": funds, "summary": summary}


@router.get("", response_model=FundsResponse)
def get_funds() -> dict:
    return _funds_payload()


@router.get("/summary", response_model=FundsSummary)
def get_funds_summary() -> dict:
    return _funds_payload()["summary"]
