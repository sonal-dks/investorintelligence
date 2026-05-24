from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta
from threading import Lock
from typing import Literal

import httpx
from fastapi import APIRouter, Header, HTTPException, Query

from backend import config
from backend.models.schemas import (
    PulseKeywordsResponse,
    PulseLatestResponse,
    PulseReviewsResponse,
    PulseTrendsResponse,
    Review,
)
from backend.services.google_docs_writer import append_weekly_pulse_page
from backend.services.pulse_summary_generator import PulseSummaryGenerator

router = APIRouter(prefix="/api/pulse", tags=["pulse"])
_generator = PulseSummaryGenerator()
_lock = Lock()
logger = logging.getLogger(__name__)

_app_reviews: list[dict] = []
_weekly_pulses: list[dict] = []
_review_keywords: list[dict] = []


def reset_state_for_tests() -> None:
    _app_reviews.clear()
    _weekly_pulses.clear()
    _review_keywords.clear()


def seed_reviews_for_tests(reviews: list[dict]) -> None:
    _app_reviews.clear()
    _app_reviews.extend(reviews)


def _ensure_seed_data() -> None:
    if _app_reviews:
        return
    now = datetime.now(UTC)
    for i in range(20):
        rating = 5 if i % 4 != 0 else 2
        _app_reviews.append(
            {
                "reviewer_name": f"User{i+1}",
                "rating": rating,
                "review_text": "Portfolio loading is slow but SIP setup is easy.",
                "review_date": (now - timedelta(days=i % 6)).date().isoformat(),
            }
        )


def _require_admin(user_role: str | None) -> None:
    if user_role != "admin":
        raise HTTPException(status_code=403, detail="admin_only")


def _sb_headers() -> dict[str, str]:
    key = config.supabase_service_role_key() or ""
    return {"apikey": key, "Authorization": f"Bearer {key}", "Content-Type": "application/json"}


def _sb_url(table: str) -> str:
    return f"{str(config.supabase_url()).rstrip('/')}/rest/v1/{table}"


def _load_latest_from_supabase() -> dict | None:
    if not config.supabase_enabled():
        return None
    try:
        r = httpx.get(
            _sb_url("weekly_pulse"),
            params={"select": "*", "order": "generated_at.desc", "limit": "1"},
            headers=_sb_headers(),
            timeout=10.0,
        )
        r.raise_for_status()
        rows = r.json() or []
        return rows[0] if rows else None
    except Exception:
        return None


def _load_keywords_from_supabase() -> list[dict] | None:
    if not config.supabase_enabled():
        return None
    try:
        latest = _load_latest_from_supabase()
        if not latest:
            return []
        r = httpx.get(
            _sb_url("review_keywords"),
            params={
                "select": "keyword,mention_count,wow_change_pct",
                "week_start": f"eq.{latest['week_start']}",
                "order": "mention_count.desc",
                "limit": "15",
            },
            headers=_sb_headers(),
            timeout=10.0,
        )
        r.raise_for_status()
        rows = r.json() or []
        enriched = []
        for row in rows:
            wow = float(row.get("wow_change_pct") or 0.0)
            enriched.append(
                {
                    "keyword": row["keyword"],
                    "mention_count": int(row.get("mention_count") or 0),
                    "wow_change_pct": wow,
                    "trend": "up" if wow > 0 else "down" if wow < 0 else "flat",
                }
            )
        return enriched
    except Exception:
        return None


def _load_trends_from_supabase() -> list[dict] | None:
    if not config.supabase_enabled():
        return None
    try:
        r = httpx.get(
            _sb_url("weekly_pulse"),
            params={
                "select": "week_start,overall_rating,total_reviews,positive_count,neutral_count,negative_count",
                "order": "week_start.desc",
                "limit": "4",
            },
            headers=_sb_headers(),
            timeout=10.0,
        )
        r.raise_for_status()
        rows = r.json() or []
        return list(reversed(rows))
    except Exception:
        return None


def _load_reviews_from_supabase(sentiment: str, page: int, limit: int) -> dict | None:
    if not config.supabase_enabled():
        return None
    try:
        params = {
            "select": "reviewer_name,rating,review_text,review_date,sentiment",
            "order": "review_date.desc",
            "limit": str(limit),
            "offset": str((page - 1) * limit),
        }
        if sentiment != "all":
            params["sentiment"] = f"eq.{sentiment}"
        r = httpx.get(_sb_url("app_reviews"), params=params, headers=_sb_headers(), timeout=10.0)
        r.raise_for_status()
        rows = r.json() or []
        count_params = {"select": "id", "limit": "1"}
        if sentiment != "all":
            count_params["sentiment"] = f"eq.{sentiment}"
        rc = httpx.get(
            _sb_url("app_reviews"),
            params=count_params,
            headers={**_sb_headers(), "Prefer": "count=exact"},
            timeout=10.0,
        )
        rc.raise_for_status()
        total = int(rc.headers.get("content-range", "0-0/0").split("/")[-1])
        return {"reviews": rows, "total": total, "page": page}
    except Exception:
        return None


def _fetch_week_reviews_from_supabase(week_start: date) -> list[dict] | None:
    if not config.supabase_enabled():
        return None
    try:
        r = httpx.get(
            _sb_url("app_reviews"),
            params={
                "select": "review_id,reviewer_name,rating,review_text,review_date,sentiment",
                "review_date": f"gte.{week_start.isoformat()}",
                "order": "review_date.desc",
                "limit": "1000",
            },
            headers=_sb_headers(),
            timeout=15.0,
        )
        r.raise_for_status()
        return r.json() or []
    except Exception:
        return None


def _persist_pulse_to_supabase(pulse: dict) -> None:
    if not config.supabase_enabled():
        return
    payload = {
        "week_start": pulse["week_start"],
        "overall_rating": pulse["overall_rating"],
        "total_reviews": pulse["total_reviews"],
        "positive_count": pulse["positive_count"],
        "neutral_count": pulse["neutral_count"],
        "negative_count": pulse["negative_count"],
        "summary_text": pulse["summary_text"],
        "action_items": pulse["action_items"],
        "themes": pulse["themes"],
        "llm_themes": pulse["llm_themes"],
        "deterministic_themes": pulse["deterministic_themes"],
        "top_themes": pulse.get("top_themes") or [],
        "user_quotes": pulse.get("user_quotes") or [],
        "llm_summary_text": pulse["llm_summary_text"],
        "deterministic_summary_text": pulse["deterministic_summary_text"],
        "model_path": pulse["model_path"],
        "model_used": pulse["model_used"],
        "deterministic_algorithm": pulse["deterministic_algorithm"],
        "judge_overall_score": pulse.get("judge_overall_score") or 0.0,
        "judge_metrics": pulse.get("judge_metrics") or {},
        "judge_rationale": pulse.get("judge_rationale") or "",
        "generated_at": pulse["generated_at"],
    }
    r = httpx.post(
        _sb_url("weekly_pulse"),
        params={"on_conflict": "week_start"},
        headers={**_sb_headers(), "Prefer": "resolution=merge-duplicates,return=representation"},
        json=payload,
        timeout=15.0,
    )
    r.raise_for_status()

    httpx.delete(
        _sb_url("review_keywords"),
        params={"week_start": f"eq.{pulse['week_start']}"},
        headers=_sb_headers(),
        timeout=10.0,
    ).raise_for_status()
    if pulse["keywords"]:
        # Keep only DB-backed columns; API-only fields like "trend" are derived on read.
        rows = []
        for row in pulse["keywords"]:
            rows.append(
                {
                    "keyword": row.get("keyword"),
                    "mention_count": row.get("mention_count"),
                    "wow_change_pct": row.get("wow_change_pct"),
                    "week_start": pulse["week_start"],
                }
            )
        httpx.post(
            _sb_url("review_keywords"),
            headers=_sb_headers(),
            json=rows,
            timeout=15.0,
        ).raise_for_status()


def _fetch_fee_scenario() -> tuple[str, list[str], list[str]]:
    if not config.supabase_enabled():
        return ("Fee explainer unavailable in this environment.", [], [])
    try:
        r = httpx.get(
            _sb_url("mutual_fund_data"),
            params={
                "select": "fund_name,expense_ratio,exit_load_text,tax_text,source_url,scraped_at",
                "order": "scraped_at.desc",
                "limit": "1",
            },
            headers=_sb_headers(),
            timeout=10.0,
        )
        r.raise_for_status()
        rows = r.json() or []
        if not rows:
            return ("No mutual_fund_data row found for fee explanation.", [], [])
        row = rows[0]
        fund = row.get("fund_name") or "Selected fund"
        exp = row.get("expense_ratio")
        exit_load = row.get("exit_load_text") or "Not specified"
        tax = row.get("tax_text") or "Tax varies by holding period and investor profile."
        fee_scenario = (
            f"{fund}: expense ratio {exp if exp is not None else 'n/a'}%, "
            f"exit load '{exit_load}'. Tax note: {tax}"
        )
        bullets = [
            "Expense ratio applies daily and reduces NAV performance over time.",
            "Exit load can reduce redemption proceeds if sold within lock/load windows.",
            "Tax treatment differs by holding period and product category.",
        ]
        source_links = [str(row.get("source_url") or "").strip()]
        return fee_scenario, bullets, [x for x in source_links if x]
    except Exception as e:
        logger.warning("fee scenario fetch failed: %s", e)
        return ("Fee explainer unavailable due to data fetch error.", [], [])


def _persist_weekly_pulse_note(
    pulse: dict,
    fee_scenario: str,
    explanation_bullets: list[str],
    source_links: list[str],
    doc_url: str | None,
) -> None:
    if not config.supabase_enabled():
        return
    payload = {
        "date": datetime.now(UTC).date().isoformat(),
        "weekly_pulse": pulse.get("summary_text") or "",
        "fee_scenario": fee_scenario,
        "explanation_bullets": explanation_bullets,
        "source_links": source_links + ([doc_url] if doc_url else []),
    }
    httpx.post(
        _sb_url("weekly_pulse_notes"),
        headers=_sb_headers(),
        json=payload,
        timeout=15.0,
    ).raise_for_status()


def _persist_review_sentiments_to_supabase(updates: list[dict]) -> None:
    if not config.supabase_enabled() or not updates:
        return
    headers = _sb_headers()
    for row in updates:
        rid = row.get("review_id")
        sent = row.get("sentiment")
        if not rid or not sent:
            continue
        r = httpx.patch(
            _sb_url("app_reviews"),
            params={"review_id": f"eq.{rid}"},
            headers=headers,
            json={"sentiment": str(sent)},
            timeout=12.0,
        )
        r.raise_for_status()


@router.get("/latest", response_model=PulseLatestResponse)
def get_latest() -> dict:
    pulse = _load_latest_from_supabase()
    if pulse is None:
        if not _weekly_pulses:
            raise HTTPException(status_code=404, detail="pulse_not_generated")
        pulse = _weekly_pulses[-1]
    payload = {k: pulse.get(k) for k in PulseLatestResponse.model_fields}
    for key in ("user_quotes", "top_themes", "llm_themes", "deterministic_themes", "themes", "action_items"):
        if payload.get(key) is None:
            payload[key] = []
    return PulseLatestResponse.model_validate(payload).model_dump()


@router.get("/reviews", response_model=PulseReviewsResponse)
def get_reviews(
    sentiment: Literal["all", "positive", "neutral", "negative"] = Query(default="all"),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
) -> dict:
    sb = _load_reviews_from_supabase(sentiment=sentiment, page=page, limit=limit)
    if sb is not None:
        return sb
    _ensure_seed_data()
    source = list(_app_reviews)
    for review in source:
        if "sentiment" not in review:
            rating = int(review.get("rating", 0))
            review["sentiment"] = "positive" if rating >= 4 else "neutral" if rating == 3 else "negative"
    if sentiment != "all":
        source = [r for r in source if r["sentiment"] == sentiment]
    total = len(source)
    start = (page - 1) * limit
    page_reviews = source[start : start + limit]
    return {"reviews": [Review(**r).model_dump() for r in page_reviews], "total": total, "page": page}


@router.get("/keywords", response_model=PulseKeywordsResponse)
def get_keywords() -> dict:
    sb = _load_keywords_from_supabase()
    if sb is not None:
        return {"keywords": sb}
    return {"keywords": _review_keywords[-15:][::-1]}


@router.get("/trends", response_model=PulseTrendsResponse)
def get_trends() -> dict:
    sb = _load_trends_from_supabase()
    if sb is not None:
        return {"trends": sb}
    rows = []
    for pulse in _weekly_pulses[-4:]:
        rows.append(
            {
                "week_start": pulse["week_start"],
                "overall_rating": pulse["overall_rating"],
                "total_reviews": pulse["total_reviews"],
                "positive_count": pulse["positive_count"],
                "neutral_count": pulse["neutral_count"],
                "negative_count": pulse["negative_count"],
            }
        )
    return {"trends": rows}


@router.post("/generate")
def generate_pulse(x_user_role: str | None = Header(default=None)) -> dict:
    _require_admin(x_user_role)
    _ensure_seed_data()
    with _lock:
        week_start = _generator.week_start()
        week_reviews = _fetch_week_reviews_from_supabase(week_start) or [
            r for r in _app_reviews if datetime.fromisoformat(str(r["review_date"])).date() >= week_start
        ]
        previous_pulse = _load_latest_from_supabase() or (_weekly_pulses[-1] if _weekly_pulses else None)
        previous_keyword_counts = (
            {row["keyword"]: row["mention_count"] for row in _review_keywords if row.get("week_start") != str(week_start)}
            if _review_keywords
            else {}
        )
        pulse = _generator.generate(
            week_reviews,
            previous_keyword_counts=previous_keyword_counts,
            previous_pulse=previous_pulse,
        )
        # Idempotent per week: replace same-week pulse.
        _weekly_pulses[:] = [p for p in _weekly_pulses if p["week_start"] != pulse["week_start"]]
        _weekly_pulses.append(pulse)
        _review_keywords[:] = [k for k in _review_keywords if k.get("week_start") != pulse["week_start"]]
        for row in pulse["keywords"]:
            _review_keywords.append({**row, "week_start": pulse["week_start"]})
        fee_scenario, fee_bullets, fee_links = _fetch_fee_scenario()

        _persist_pulse_to_supabase(pulse)
        _persist_review_sentiments_to_supabase(pulse.get("review_sentiment_updates") or [])
        doc_url = None
        doc_id = config.weekly_pulse_google_doc_id()
        if doc_id:
            try:
                doc_url = append_weekly_pulse_page(
                    doc_id=doc_id,
                    week_start=str(pulse["week_start"]),
                    summary_text=str(pulse.get("summary_text") or ""),
                    top_themes=list(pulse.get("top_themes") or []),
                    action_items=list(pulse.get("action_items") or []),
                    fee_scenario=fee_scenario,
                    explanation_bullets=fee_bullets,
                    source_links=fee_links,
                )
            except Exception as e:
                logger.warning("google docs append failed: %s", e)
        _persist_weekly_pulse_note(
            pulse=pulse,
            fee_scenario=fee_scenario,
            explanation_bullets=fee_bullets,
            source_links=fee_links,
            doc_url=doc_url,
        )
        return {
            "status": "ok",
            "week_start": pulse["week_start"],
            "judge": pulse["judge"],
            "total_reviews": pulse["total_reviews"],
            "judge_overall_score": pulse.get("judge_overall_score") or 0.0,
            "doc_url": doc_url,
        }
