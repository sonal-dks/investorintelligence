from __future__ import annotations

from backend.services.pulse_ops_contract import validate_weekly_pulse_contract
from backend.services.pulse_summary_generator import PulseSummaryGenerator
from backend.services.sentiment_analyzer import SentimentAnalyzer


class _LLMOkContract:
    def is_enabled(self) -> bool:
        return True

    def classify_review_sentiments(self, reviews, batch_size=24):
        return SentimentAnalyzer().annotate(list(reviews))

    def generate(self, review_snippets, stats):
        class _Res:
            summary_text = (
                "Weekly review volume was steady with mixed sentiment across SIP, performance, and support. "
                "Users praised fund selection while asking for faster loads and clearer navigation. "
                "No major incidents surfaced in-store comments this cycle."
            )
            action_items = [
                "Prioritize portfolio load time on low-end Android devices.",
                "Ship a dark mode beta aligned with top-requested UX feedback.",
                "Audit SIP edit flows against the highest-friction support tickets.",
            ]
            themes = [
                {"theme": "SIP Workflow", "count": 12, "sentiment": "negative"},
                {"theme": "App Performance", "count": 9, "sentiment": "neutral"},
                {"theme": "Support Experience", "count": 7, "sentiment": "negative"},
                {"theme": "UI/UX", "count": 5, "sentiment": "positive"},
            ]
            model_used = "test/primary"
            model_path = "primary_llm"

        return _Res()


def _diverse_reviews(n: int) -> list[dict]:
    templates = [
        ("The SIP workflow is confusing when I try to modify installment amounts on my mutual funds.", 4),
        ("App feels slow when loading my portfolio dashboard each morning before market open.", 2),
        ("Please add proper dark mode for late night portfolio checking and readability.", 5),
        ("Customer support was unhelpful with my KYC documentation problem last Tuesday.", 2),
        ("Great fund catalog overall but the UI needs polish and clearer navigation between screens.", 4),
    ]
    reviews = []
    for i in range(n):
        text, rating = templates[i % len(templates)]
        reviews.append(
            {
                "reviewer_name": f"User{i}",
                "rating": rating,
                "review_text": text,
                "review_date": "2026-05-08",
            }
        )
    return reviews


def test_ops_contract_passes_on_full_pulse_with_llm_mock():
    gen = PulseSummaryGenerator(llm_client=_LLMOkContract())
    reviews = _diverse_reviews(14)
    pulse = gen.generate(reviews=reviews, previous_keyword_counts={}, previous_pulse=None)
    result = validate_weekly_pulse_contract(pulse, reviews)
    assert result["pass"] is True, result["issues"]
    assert result["word_count"] <= 250


def test_ops_contract_rejects_more_than_five_themes():
    pulse = {
        "total_reviews": 20,
        "summary_text": "x " * 120,
        "action_items": ["a", "b", "c"],
        "llm_themes": [{"theme": f"T{i}", "count": i, "sentiment": "neutral"} for i in range(1, 7)],
        "deterministic_themes": [],
        "top_themes": [],
        "user_quotes": ["short", "short", "short"],
    }
    r = validate_weekly_pulse_contract(pulse, [])
    assert r["pass"] is False
    assert "themes_exceed_max_5" in r["issues"]


def test_ops_contract_rejects_pii_in_summary():
    pulse = {
        "total_reviews": 15,
        "summary_text": "Contact us at user@example.com for follow up.",
        "action_items": ["a", "b", "c"],
        "llm_themes": [
            {"theme": "A", "count": 5, "sentiment": "neutral"},
            {"theme": "B", "count": 4, "sentiment": "neutral"},
            {"theme": "C", "count": 3, "sentiment": "neutral"},
        ],
        "deterministic_themes": [],
        "top_themes": [
            {"theme": "A", "count": 5, "sentiment": "neutral"},
            {"theme": "B", "count": 4, "sentiment": "neutral"},
            {"theme": "C", "count": 3, "sentiment": "neutral"},
        ],
        "user_quotes": [
            "The SIP workflow is confusing when I try to modify installment amounts on my mutual funds.",
            "App feels slow when loading my portfolio dashboard each morning before market open.",
            "Please add proper dark mode for late night portfolio checking and readability.",
        ],
    }
    reviews = _diverse_reviews(15)
    r = validate_weekly_pulse_contract(pulse, reviews)
    assert r["pass"] is False
    assert "pii_in_output" in r["issues"]


def test_ops_contract_low_volume_path():
    pulse = {
        "total_reviews": 3,
        "summary_text": "Insufficient data this week. Fewer than 10 new reviews were available.",
        "action_items": ["x", "y", "z"],
        "llm_themes": [],
        "deterministic_themes": [],
        "top_themes": [],
        "user_quotes": [],
    }
    r = validate_weekly_pulse_contract(pulse, [])
    assert r["pass"] is True, r["issues"]
