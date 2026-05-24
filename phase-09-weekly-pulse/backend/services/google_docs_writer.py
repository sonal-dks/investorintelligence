from __future__ import annotations

import json
import os
from typing import Any

from backend import config


def _credentials_from_env():
    from google.oauth2 import service_account

    raw = config.google_service_account_json()
    if not raw:
        raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON not configured")

    scopes = [
        "https://www.googleapis.com/auth/documents",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    if raw.strip().startswith("{"):
        info = json.loads(raw)
        return service_account.Credentials.from_service_account_info(info, scopes=scopes)
    if os.path.exists(raw):
        return service_account.Credentials.from_service_account_file(raw, scopes=scopes)
    raise RuntimeError("GOOGLE_SERVICE_ACCOUNT_JSON must be JSON content or an existing file path")


def append_weekly_pulse_page(
    *,
    doc_id: str,
    week_start: str,
    summary_text: str,
    top_themes: list[dict],
    action_items: list[str],
    fee_scenario: str,
    explanation_bullets: list[str],
    source_links: list[str],
) -> str:
    from googleapiclient.discovery import build

    creds = _credentials_from_env()
    docs = build("docs", "v1", credentials=creds, cache_discovery=False)
    title = f"Weekly Pulse — {week_start}"
    lines: list[str] = [
        "",
        "",
        title,
        "",
        "Weekly pulse",
        summary_text,
        "",
        "Top themes",
    ]
    for t in top_themes[:3]:
        lines.append(f"- {t.get('theme', '')} ({t.get('count', 0)}) [{t.get('sentiment', 'neutral')}]")
    lines.extend(["", "Action ideas"])
    for i, item in enumerate(action_items[:3], start=1):
        lines.append(f"{i}. {item}")
    lines.extend(["", "Fee explanation", fee_scenario, "", "Explanation bullets"])
    for b in explanation_bullets[:6]:
        lines.append(f"- {b}")
    lines.extend(["", "Source links"])
    for l in source_links[:6]:
        lines.append(f"- {l}")
    text = "\n".join(lines) + "\n"

    docs.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {"insertPageBreak": {"location": {"index": 1}}},
                {"insertText": {"location": {"index": 1}, "text": text}},
            ]
        },
    ).execute()
    return f"https://docs.google.com/document/d/{doc_id}/edit"

