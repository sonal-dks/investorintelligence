from __future__ import annotations

from datetime import UTC, date, datetime, timedelta

from backend.services.keyword_tracker import KeywordTracker
from backend.services.llm_client import PulseLLMClient
from backend.services.pulse_judge import PulseJudge
from backend.services.sentiment_analyzer import SentimentAnalyzer
from backend.services.theme_extractor import ThemeExtractor


class PulseSummaryGenerator:
    def __init__(
        self,
        sentiment_analyzer: SentimentAnalyzer | None = None,
        theme_extractor: ThemeExtractor | None = None,
        keyword_tracker: KeywordTracker | None = None,
        pulse_judge: PulseJudge | None = None,
        llm_client: PulseLLMClient | None = None,
    ) -> None:
        self._sentiment = sentiment_analyzer or SentimentAnalyzer()
        self._themes = theme_extractor or ThemeExtractor()
        self._keywords = keyword_tracker or KeywordTracker()
        self._judge = pulse_judge or PulseJudge()
        self._llm = llm_client or PulseLLMClient()

    def week_start(self, now: datetime | None = None) -> date:
        now = now or datetime.now(UTC)
        return (now - timedelta(days=now.weekday())).date()

    def generate(
        self,
        reviews: list[dict],
        previous_keyword_counts: dict[str, int] | None = None,
        previous_pulse: dict | None = None,
        now: datetime | None = None,
    ) -> dict:
        week_start = self.week_start(now)
        annotated = self._sentiment.annotate(reviews)
        total = len(annotated)
        positive = sum(1 for r in annotated if r["sentiment"] == "positive")
        neutral = sum(1 for r in annotated if r["sentiment"] == "neutral")
        negative = sum(1 for r in annotated if r["sentiment"] == "negative")
        overall = round((sum(int(r.get("rating", 0)) for r in annotated) / total), 2) if total else 0.0

        deterministic_themes, deterministic_summary, deterministic_actions = self._deterministic_outputs(
            annotated=annotated,
            total=total,
            overall=overall,
            positive=positive,
            negative=negative,
            previous_pulse=previous_pulse,
        )

        summary = deterministic_summary
        action_items = deterministic_actions
        llm_themes = previous_pulse.get("llm_themes", []) if previous_pulse else []
        model_path = "deterministic_fallback"
        model_used = "none"

        llm_summary_text = deterministic_summary

        if total >= 10:
            snippets = [str(r.get("review_text", ""))[:500] for r in annotated]
            stats = {
                "total_reviews": total,
                "overall_rating": overall,
                "positive_count": positive,
                "neutral_count": neutral,
                "negative_count": negative,
            }
            try:
                llm_result = self._llm.generate(review_snippets=snippets, stats=stats)
                summary = llm_result.summary_text
                llm_summary_text = llm_result.summary_text
                action_items = llm_result.action_items
                llm_themes = llm_result.themes
                model_path = llm_result.model_path
                model_used = llm_result.model_used
            except Exception:
                pass
        else:
            llm_themes = previous_pulse.get("llm_themes", []) if previous_pulse else []

        keywords = self._keywords.compute(annotated, previous_counts=previous_keyword_counts or {})
        verdict = self._judge.validate(summary, action_items)

        # Controlled degradation to keep storage contract valid if LLM response is malformed.
        if not verdict["pass"]:
            summary = deterministic_summary
            action_items = deterministic_actions
            verdict = self._judge.validate(summary, action_items)
            model_path = "deterministic_fallback"
            model_used = "none"

        # LLM themes are the only themes shared for email/voice downstream use.
        themes = llm_themes

        payload = {
            "week_start": str(week_start),
            "overall_rating": overall,
            "total_reviews": total,
            "positive_count": positive,
            "neutral_count": neutral,
            "negative_count": negative,
            "summary_text": summary,
            "action_items": action_items,
            "themes": themes,
            "llm_themes": llm_themes,
            "deterministic_themes": deterministic_themes,
            "llm_summary_text": llm_summary_text,
            "deterministic_summary_text": deterministic_summary,
            "model_path": model_path,
            "model_used": model_used,
            "deterministic_algorithm": "rule-based sentiment + frequency theme extraction + keyword WoW",
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "judge": verdict,
            "keywords": keywords,
        }
        return payload

    def _deterministic_outputs(
        self,
        annotated: list[dict],
        total: int,
        overall: float,
        positive: int,
        negative: int,
        previous_pulse: dict | None,
    ) -> tuple[list[dict], str, list[str]]:
        if total < 10:
            deterministic_summary = "Insufficient data this week. Fewer than 10 new reviews were available."
            deterministic_actions = [
                "Continue collecting user feedback for stronger trend confidence.",
                "Review prior week's top issue themes for continuity.",
                "Re-run pulse generation after next scrape cycle.",
            ]
            deterministic_themes = previous_pulse.get("deterministic_themes", []) if previous_pulse else []
            return deterministic_themes, deterministic_summary, deterministic_actions

        deterministic_themes = self._themes.extract(annotated, limit=5)
        lead_theme = deterministic_themes[0]["theme"] if deterministic_themes else "General Product Feedback"
        deterministic_summary = (
            f"This week we processed {total} reviews with an average rating of {overall}. "
            f"Positive sentiment led at {positive}, while {negative} reviews highlighted friction points. "
            f"The top recurring theme was {lead_theme}. Users also requested improvements in reliability, "
            "navigation clarity, and feature discoverability. Priorities should focus on fixing recurring pain "
            "points while preserving strengths called out in positive feedback."
        )
        deterministic_actions = [
            f"Address the highest-frequency issue under {lead_theme} this sprint.",
            "Publish one UX improvement focused on reducing repeat complaint patterns.",
            "Track post-release sentiment shift against next week's pulse baseline.",
        ]
        return deterministic_themes, deterministic_summary, deterministic_actions
