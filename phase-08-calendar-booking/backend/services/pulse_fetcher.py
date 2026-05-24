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
                "select": "week_start,summary_text,action_items,llm_themes,generated_at,judge_overall_score,judge_metrics",
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
        note = None
        rn = httpx.get(
            f"{url.rstrip('/')}/rest/v1/weekly_pulse_notes",
            params={"select": "fee_scenario,explanation_bullets,source_links,created_at", "order": "created_at.desc", "limit": "1"},
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=10.0,
        )
        if rn.status_code < 400:
            rows_n = rn.json() or []
            note = rows_n[0] if rows_n else None
        doc_url = None
        if note:
            links = note.get("source_links") or []
            if isinstance(links, list):
                for l in links:
                    s = str(l or "")
                    if "docs.google.com/document" in s:
                        doc_url = s
                        break
        return WeeklyPulseSnapshot(
            week_start=row.get("week_start"),
            summary_text=row.get("summary_text") or "",
            action_items=list(items) if isinstance(items, list) else [],
            themes=themes,
            generated_at=gen_s,
            judge_overall_score=float(row.get("judge_overall_score") or 0.0),
            judge_metrics=row.get("judge_metrics") or {},
            doc_url=doc_url,
            fee_scenario=(note or {}).get("fee_scenario"),
            explanation_bullets=list((note or {}).get("explanation_bullets") or []),
        )
    except Exception:
        return None
