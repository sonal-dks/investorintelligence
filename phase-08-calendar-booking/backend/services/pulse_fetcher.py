from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import httpx

from backend import config
from backend.models.schemas import WeeklyPulseSnapshot


def fetch_latest_pulse() -> WeeklyPulseSnapshot | None:
    url = config.supabase_url()
    key = config.supabase_service_role_key()
    if not url or not key:
        return None
    try:
        r = httpx.get(
            f"{url.rstrip('/')}/rest/v1/weekly_pulse",
            params={
                "select": "week_start,summary_text,action_items,llm_themes,generated_at",
                "order": "generated_at.desc",
                "limit": "1",
            },
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=10.0,
        )
        r.raise_for_status()
        rows = r.json()
        if not rows:
            return None
        row = rows[0]
        gen_s = row.get("generated_at") or ""
        if not gen_s:
            return None
        gen = datetime.fromisoformat(gen_s.replace("Z", "+00:00"))
        if gen.tzinfo is None:
            gen = gen.replace(tzinfo=UTC)
        if datetime.now(UTC) - gen > timedelta(days=14):
            return None
        items = row.get("action_items") or []
        if isinstance(items, str):
            items = []
        themes = row.get("llm_themes") or []
        if not isinstance(themes, list):
            themes = []
        return WeeklyPulseSnapshot(
            week_start=row.get("week_start"),
            summary_text=row.get("summary_text") or "",
            action_items=list(items) if isinstance(items, list) else [],
            themes=themes,
            generated_at=gen_s,
        )
    except Exception:
        return None
