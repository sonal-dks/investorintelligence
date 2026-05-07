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
def use_mock_calendar() -> bool:
    return os.getenv("PHASE08_USE_MOCK_CALENDAR", "0").lower() in ("1", "true", "yes")


@lru_cache
def use_mock_gmail() -> bool:
    return os.getenv("PHASE08_USE_MOCK_GMAIL", "0").lower() in ("1", "true", "yes")


def google_calendar_id() -> str | None:
    return os.getenv("GOOGLE_CALENDAR_ID")


def google_service_account_json() -> str | None:
    return os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")


def gmail_client_id() -> str | None:
    return os.getenv("GMAIL_CLIENT_ID")


def gmail_client_secret() -> str | None:
    return os.getenv("GMAIL_CLIENT_SECRET")


def gmail_refresh_token() -> str | None:
    return os.getenv("GMAIL_REFRESH_TOKEN")


def gmail_from_address() -> str | None:
    return os.getenv("GMAIL_FROM_ADDRESS")


def advisor_email() -> str | None:
    return os.getenv("ADVISOR_EMAIL")


def supabase_url() -> str | None:
    return os.getenv("SUPABASE_URL")


def supabase_service_role_key() -> str | None:
    return os.getenv("SUPABASE_SERVICE_ROLE_KEY")


def email_template_path() -> str:
    return os.getenv(
        "BOOKING_EMAIL_TEMPLATE_PATH",
        "Docs/Architecture/Email-Templates/booking_confirmation_email.md",
    )


def project_root() -> str:
    """Repo root (parent of phase-08-calendar-booking)."""
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def resolved_template_path() -> str:
    p = email_template_path()
    if os.path.isabs(p):
        return p
    return os.path.join(project_root(), p)
