from __future__ import annotations

from datetime import UTC, datetime, timedelta

from supabase import Client


class PulseThemeService:
    """Reads LLM-only themes from latest weekly_pulse row."""

    def __init__(self, supabase: Client) -> None:
        self._client = supabase

    def get_latest_llm_theme(self) -> str | None:
        rows = (
            self._client.table("weekly_pulse")
            .select("llm_themes,themes,generated_at")
            .order("generated_at", desc=True)
            .limit(1)
            .execute()
            .data
            or []
        )
        if not rows:
            return None
        row = rows[0]
        generated_at = row.get("generated_at")
        if generated_at:
            gen = datetime.fromisoformat(str(generated_at).replace("Z", "+00:00"))
            if gen.tzinfo is None:
                gen = gen.replace(tzinfo=UTC)
            if datetime.now(UTC) - gen > timedelta(days=14):
                return None
        themes = row.get("llm_themes") or row.get("themes") or []
        if not isinstance(themes, list) or not themes:
            return None
        top = themes[0]
        return str(top.get("theme") or "").strip() or None
