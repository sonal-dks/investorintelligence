from __future__ import annotations

from backend.services.keyword_tracker import KeywordTracker
from backend.services.pulse_judge import PulseJudge
from backend.services.pulse_summary_generator import PulseSummaryGenerator
from backend.services.sentiment_analyzer import SentimentAnalyzer


def test_sentiment_analyzer_star_mapping():
    analyzer = SentimentAnalyzer()
    assert analyzer.classify_rating(5) == "positive"
    assert analyzer.classify_rating(4) == "positive"
    assert analyzer.classify_rating(3) == "neutral"
    assert analyzer.classify_rating(2) == "negative"
    assert analyzer.classify_rating(1) == "negative"


def test_keyword_tracker_wow_change():
    tracker = KeywordTracker()
    rows = tracker.compute(
        reviews=[{"review_text": "loading loading slow sip"}, {"review_text": "sip issue"}],
        previous_counts={"loading": 1, "sip": 4},
    )
    row_map = {r["keyword"]: r for r in rows}
    assert row_map["loading"]["wow_change_pct"] == 100.0
    assert row_map["sip"]["wow_change_pct"] == -50.0


def test_pulse_judge_enforces_constraints():
    judge = PulseJudge()
    verdict = judge.validate("ok summary", ["a", "b", "c"])
    assert verdict["pass"] is True
    too_many_words = "w " * 251
    verdict_fail = judge.validate(too_many_words, ["a", "b"])
    assert verdict_fail["pass"] is False
    assert "summary_word_count_exceeds_250" in verdict_fail["issues"]
    assert "action_items_must_be_exactly_3" in verdict_fail["issues"]


def test_generator_insufficient_data_fallback():
    generator = PulseSummaryGenerator()
    pulse = generator.generate(reviews=[{"rating": 5, "review_text": "great", "review_date": "2026-05-05"}])
    assert pulse["total_reviews"] == 1
    assert "Insufficient data" in pulse["summary_text"]
    assert len(pulse["action_items"]) == 3


class _LLMOk:
    def is_enabled(self) -> bool:
        return True

    def classify_review_sentiments(self, reviews, batch_size=24):
        return SentimentAnalyzer().annotate(list(reviews))

    def generate(self, review_snippets, stats):
        class _Res:
            summary_text = "LLM weekly pulse summary under constraints."
            action_items = ["A1", "A2", "A3"]
            themes = [{"theme": "LLM Theme", "count": 12, "sentiment": "mixed"}]
            model_used = "test/primary"
            model_path = "primary_llm"

        return _Res()


class _LLMFail:
    def is_enabled(self) -> bool:
        return True

    def classify_review_sentiments(self, reviews, batch_size=24):
        raise RuntimeError("llm sentiment failed")

    def generate(self, review_snippets, stats):
        raise RuntimeError("llm failed")


def test_generator_prefers_llm_then_exposes_det_comparison():
    generator = PulseSummaryGenerator(llm_client=_LLMOk())
    reviews = [{"rating": 5, "review_text": "great app with loading issue", "review_date": "2026-05-05"} for _ in range(12)]
    pulse = generator.generate(reviews=reviews)
    assert pulse["summary_text"] == "LLM weekly pulse summary under constraints."
    assert pulse["themes"] == pulse["llm_themes"]
    assert pulse["deterministic_summary_text"] != ""
    assert pulse["model_path"] == "primary_llm"


def test_generator_falls_back_to_deterministic_when_llm_fails():
    generator = PulseSummaryGenerator(llm_client=_LLMFail())
    reviews = [{"rating": 5, "review_text": "great app with loading issue", "review_date": "2026-05-05"} for _ in range(12)]
    pulse = generator.generate(reviews=reviews)
    assert pulse["model_path"] == "deterministic_fallback"
    assert pulse["summary_text"] == pulse["deterministic_summary_text"]
