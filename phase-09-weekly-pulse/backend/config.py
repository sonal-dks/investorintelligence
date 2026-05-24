from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv

    _ENV_DIR = Path(__file__).resolve().parent.parent
    _REPO_ROOT = _ENV_DIR.parent
    load_dotenv(_ENV_DIR / ".env", override=False)
    _asm = _REPO_ROOT / "phase-12-assembly-deploy"
    if (_asm / ".env").exists():
        load_dotenv(_asm / ".env", override=False)
    _ll = _REPO_ROOT / "longlist.env"
    if _ll.exists():
        load_dotenv(_ll, override=False)
except ImportError:
    pass


@lru_cache
def supabase_url() -> str | None:
    return os.getenv("SUPABASE_URL")


@lru_cache
def supabase_service_role_key() -> str | None:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def supabase_enabled() -> bool:
    if os.getenv("PHASE09_DISABLE_SUPABASE", "0").lower() in ("1", "true", "yes"):
        return False
    return bool(supabase_url() and supabase_service_role_key())


@lru_cache
def google_service_account_json() -> str | None:
    return os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")


@lru_cache
def weekly_pulse_google_doc_id() -> str | None:
    return os.getenv("WEEKLY_PULSE_GOOGLE_DOC_ID")
