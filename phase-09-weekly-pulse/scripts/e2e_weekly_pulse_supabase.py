#!/usr/bin/env python3
"""
End-to-end Weekly Pulse: live Supabase app_reviews -> generate -> persist -> latest -> ops contract.

Run from repo:  cd phase-09-weekly-pulse && python3 scripts/e2e_weekly_pulse_supabase.py

Requires: SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY (e.g. via .env or longlist.env).
Needs >=10 rows in app_reviews with review_date in the current ISO week (week_start Monday).
"""
from __future__ import annotations

import os
import sys
from pathlib import Path


def _load_env() -> Path:
    phase_root = Path(__file__).resolve().parent.parent
    os.chdir(phase_root)
    try:
        from dotenv import load_dotenv

        load_dotenv(phase_root / ".env", override=False)
        asm = phase_root.parent / "phase-12-assembly-deploy"
        if (asm / ".env").exists():
            load_dotenv(asm / ".env", override=False)
        ll = phase_root.parent / "longlist.env"
        if ll.exists():
            load_dotenv(ll, override=False)
    except ImportError:
        pass
    return phase_root


def main() -> int:
    phase_root = _load_env()
    sys.path.insert(0, str(phase_root))
    os.environ.pop("PHASE09_DISABLE_SUPABASE", None)

    if not os.getenv("SUPABASE_URL") or not os.getenv("SUPABASE_SERVICE_ROLE_KEY"):
        print(
            "ERROR: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set (e.g. longlist.env or phase .env).",
            file=sys.stderr,
        )
        return 1

    # Imports after env so backend.config sees real Supabase flags.
    from fastapi.testclient import TestClient

    from backend.main import app
    from backend.routers.pulse_router import _fetch_week_reviews_from_supabase
    from backend.services.pulse_ops_contract import validate_weekly_pulse_contract
    from backend.services.pulse_summary_generator import PulseSummaryGenerator

    gen = PulseSummaryGenerator()
    week_start = gen.week_start()
    reviews = _fetch_week_reviews_from_supabase(week_start)
    if reviews is None:
        print("ERROR: failed to fetch app_reviews from Supabase for this week.", file=sys.stderr)
        return 1
    n = len(reviews)
    if n < 10:
        print(
            f"ERROR: E2E needs >=10 app_reviews with review_date >= {week_start} (got {n}). "
            "Ingest reviews first (Phase 01) or wait for more data.",
            file=sys.stderr,
        )
        return 1

    client = TestClient(app)
    rg = client.post("/api/pulse/generate", headers={"x-user-role": "admin"})
    if rg.status_code != 200:
        print(rg.text, file=sys.stderr)
        return 1
    judge = rg.json().get("judge") or {}
    if not judge.get("pass"):
        print(f"ERROR: pulse judge failed: {judge}", file=sys.stderr)
        return 1

    latest = client.get("/api/pulse/latest")
    if latest.status_code != 200:
        print(latest.text, file=sys.stderr)
        return 1
    body = latest.json()

    v = validate_weekly_pulse_contract(body, reviews)
    if not v["pass"]:
        print(f"ERROR: ops contract failed: {v.get('issues')}", file=sys.stderr)
        return 1

    if not (body.get("llm_themes") or []):
        print("ERROR: llm_themes is empty after generation.", file=sys.stderr)
        return 1
    if float(body.get("judge_overall_score") or 0) <= 0:
        print("ERROR: judge_overall_score missing/zero.", file=sys.stderr)
        return 1

    print(
        f"OK: weekly pulse E2E passed ({n} reviews week>={week_start}, "
        f"quotes={len(body.get('user_quotes') or [])}, top_themes={len(body.get('top_themes') or [])}, "
        f"judge={body.get('judge_overall_score')})"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
