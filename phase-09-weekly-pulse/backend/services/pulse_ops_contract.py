from __future__ import annotations

import re
from typing import Any

# Operational weekly pulse contract (product QA / guardrails).

_PII_EMAIL = re.compile(r"\S+@\S+\.\S+|\S+@\S+")
_PII_DIGITS = re.compile(r"\d{10,}")


def normalize_ws(text: str) -> str:
    return " ".join(text.split())


def text_has_pii(text: str) -> bool:
    if not text or not str(text).strip():
        return False
    s = str(text)
    if _PII_EMAIL.search(s):
        return True
    if "@" in s:
        return True
    return bool(_PII_DIGITS.search(s))


def _primary_themes(pulse: dict[str, Any]) -> list[dict[str, Any]]:
    llm = pulse.get("llm_themes") or []
    det = pulse.get("deterministic_themes") or []
    return list(llm) if llm else list(det)


def _theme_row_key(row: dict[str, Any]) -> tuple[str, int, str]:
    try:
        c = int(row.get("count", 0))
    except (TypeError, ValueError):
        c = 0
    return (str(row.get("theme")), c, str(row.get("sentiment")))


def _expected_top_themes(primary: list[dict[str, Any]]) -> list[dict[str, Any]]:
    def count_key(row: dict[str, Any]) -> int:
        try:
            return int(row.get("count", 0))
        except (TypeError, ValueError):
            return 0

    ranked = sorted(primary, key=lambda x: -count_key(x))
    return ranked[:3]


def _quotes_are_verbatim(quotes: list[str], source_reviews: list[dict[str, Any]]) -> bool:
    bodies = [normalize_ws(str(r.get("review_text", ""))) for r in source_reviews]
    for q in quotes:
        qn = normalize_ws(q)
        if len(qn) < 15:
            return False
        if not any(qn in body for body in bodies):
            return False
    return True


def _outputs_pii_free(pulse: dict[str, Any], primary: list[dict[str, Any]], top: list[dict[str, Any]]) -> bool:
    chunks: list[str] = [str(pulse.get("summary_text") or "")]
    chunks.extend(str(x) for x in (pulse.get("action_items") or []))
    for row in primary + top:
        chunks.append(str(row.get("theme") or ""))
    chunks.extend(str(x) for x in (pulse.get("user_quotes") or []))
    return not any(text_has_pii(c) for c in chunks)


def validate_weekly_pulse_contract(pulse: dict[str, Any], source_reviews: list[dict[str, Any]]) -> dict[str, Any]:
    """
    Enforce explicit weekly pulse rules:
    - >=10 reviews: max 5 theme groups, top 3 identified, 3 verbatim quotes,
      summary <= 250 words, exactly 3 action items, no PII in surfaced text.
    - <10 reviews: insufficient-data summary marker, 3 actions, no PII.
    """
    issues: list[str] = []
    total = int(pulse.get("total_reviews") or 0)
    summary = str(pulse.get("summary_text") or "")
    actions = list(pulse.get("action_items") or [])
    words = [w for w in summary.split() if w.strip()]
    primary = _primary_themes(pulse)

    if total < 10:
        if "Insufficient data" not in summary:
            issues.append("low_volume_must_state_insufficient_data")
        if len(actions) != 3:
            issues.append("action_items_must_be_exactly_3")
        if not summary.strip():
            issues.append("summary_empty")
        if not _outputs_pii_free(pulse, primary, pulse.get("top_themes") or []):
            issues.append("pii_in_output")
        return {"pass": len(issues) == 0, "issues": issues, "word_count": len(words)}

    if len(words) > 250:
        issues.append("summary_word_count_exceeds_250")
    if len(actions) != 3:
        issues.append("action_items_must_be_exactly_3")
    if not summary.strip():
        issues.append("summary_empty")

    if len(primary) > 5:
        issues.append("themes_exceed_max_5")
    if len(primary) < 3:
        issues.append("must_group_into_at_least_3_themes")

    expected_top = _expected_top_themes(primary)
    top = list(pulse.get("top_themes") or [])
    if [_theme_row_key(r) for r in top] != [_theme_row_key(r) for r in expected_top]:
        issues.append("top_themes_must_be_top_3_by_count")

    quotes = list(pulse.get("user_quotes") or [])
    if len(quotes) != 3:
        issues.append("must_extract_exactly_3_user_quotes")
    elif not _quotes_are_verbatim(quotes, source_reviews):
        issues.append("quotes_must_be_verbatim_from_source_reviews")

    if not _outputs_pii_free(pulse, primary, expected_top):
        issues.append("pii_in_output")

    return {"pass": len(issues) == 0, "issues": issues, "word_count": len(words)}
