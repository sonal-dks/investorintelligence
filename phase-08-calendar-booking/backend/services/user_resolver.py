from __future__ import annotations

from typing import Any

import httpx

from backend import config


def resolve_user(user_id: str) -> tuple[str, str]:
    """Returns (email, display_name)."""
    import os

    override = os.getenv("PHASE08_TEST_USER_EMAIL")
    if override:
        name = os.getenv("PHASE08_TEST_USER_NAME", "Test User")
        return override, name

    url = config.supabase_url()
    key = config.supabase_service_role_key()
    if not url or not key:
        raise RuntimeError(
            "Cannot resolve user without SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
            "(or set PHASE08_TEST_USER_EMAIL for local tests)"
        )

    r = httpx.get(
        f"{url.rstrip('/')}/auth/v1/admin/users/{user_id}",
        headers={"apikey": key, "Authorization": f"Bearer {key}"},
        timeout=10.0,
    )
    r.raise_for_status()
    data: dict[str, Any] = r.json()
    email = (data.get("email") or "").strip()
    if not email:
        raise ValueError("User has no email in Supabase Auth")
    meta = data.get("user_metadata") or {}
    name = meta.get("full_name") or meta.get("name") or email.split("@", 1)[0]
    return email, str(name)
