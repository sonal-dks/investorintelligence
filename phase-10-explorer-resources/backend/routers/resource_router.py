from __future__ import annotations

import httpx
from fastapi import APIRouter

from backend import config
from backend.models.schemas import FeeExplainerResponse
from backend.services.fee_explainer_service import FeeExplainerService

router = APIRouter(prefix="/api/resources", tags=["resources"])
_service = FeeExplainerService()


def _sb_headers() -> dict[str, str]:
    key = config.supabase_service_role_key() or ""
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _sb_url(table: str) -> str:
    return f"{str(config.supabase_url()).rstrip('/')}/rest/v1/{table}"


def _load_fee_rows() -> list[dict] | None:
    if not config.supabase_enabled():
        return None
    try:
        r = httpx.get(
            _sb_url("fee_explainer_data"),
            params={"select": "*", "order": "last_updated.desc", "limit": "500"},
            headers=_sb_headers(),
            timeout=10.0,
        )
        r.raise_for_status()
        return r.json() or []
    except Exception:
        return None


@router.get("/fees", response_model=FeeExplainerResponse)
def get_fee_explainer() -> dict:
    rows = _load_fee_rows()
    if rows is None:
        rows = _service.sample_rows()
    return _service.build_sections(rows)
