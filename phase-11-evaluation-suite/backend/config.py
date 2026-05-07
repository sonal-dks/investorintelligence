from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def supabase_url() -> str | None:
    return os.getenv("SUPABASE_URL")


def supabase_service_role_key() -> str | None:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def supabase_enabled() -> bool:
    if os.getenv("PHASE11_DISABLE_SUPABASE", "").lower() in {"1", "true", "yes"}:
        return False
    return bool(supabase_url() and supabase_service_role_key())


def openrouter_api_key() -> str | None:
    return os.getenv("OPENROUTER_API_KEY")


def openrouter_primary_model() -> str:
    return os.getenv("OPENROUTER_PRIMARY_MODEL", "anthropic/claude-sonnet-4.5")


def openrouter_judge_model() -> str:
    return os.getenv("OPENROUTER_JUDGE_MODEL", "openai/gpt-4o-mini")


def eval_target_chat_url() -> str | None:
    return os.getenv("EVAL_TARGET_CHAT_URL")


def eval_target_chat_auth_token() -> str | None:
    return os.getenv("EVAL_TARGET_CHAT_AUTH_TOKEN")
