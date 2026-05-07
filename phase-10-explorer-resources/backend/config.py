from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

try:
    from dotenv import load_dotenv

    _ENV_DIR = Path(__file__).resolve().parent.parent
    load_dotenv(_ENV_DIR / ".env", override=False)
except ImportError:
    pass


@lru_cache
def supabase_url() -> str | None:
    return os.getenv("SUPABASE_URL")


@lru_cache
def supabase_service_role_key() -> str | None:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def supabase_enabled() -> bool:
    if os.getenv("PHASE10_DISABLE_SUPABASE", "0").lower() in ("1", "true", "yes"):
        return False
    return bool(supabase_url() and supabase_service_role_key())
