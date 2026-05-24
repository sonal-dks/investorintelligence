from __future__ import annotations

import logging
from datetime import UTC, date, datetime, timedelta

from backend.services.keyword_tracker import KeywordTracker
from backend.services.llm_client import PulseLLMClient
from backend.services.pulse_judge import PulseJudge
from backend.services.quote_extractor import QuoteExtractor
from backend.services.sentiment_analyzer import SentimentAnalyzer
from backend.services.theme_extractor import ThemeExtractor

logger = logging.getLogger(__name__)


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
        self._quotes = QuoteExtractor()
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
        annotated: list[dict]
        llm_enabled = bool(getattr(self._llm, "is_enabled", lambda: False)())
        if len(reviews) >= 10 and llm_enabled:
            try:
                annotated = self._llm.classify_review_sentiments(list(reviews), batch_size=24)
            except Exception as e:
                logger.warning("LLM review sentiment failed; using star ratings: %s", e)
                annotated = self._sentiment.annotate(reviews)
        else:
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

        judge_score = 0.0
        judge_metrics: dict = {}
        judge_rationale = ""

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
                llm_themes = self._cap_normalize_themes(llm_result.themes, cap=5)
                # Group overly specific themes into dashboard-friendly clusters.
                if llm_themes and hasattr(self._llm, "group_themes"):
                    grouped = self._llm.group_themes(llm_themes, snippets, max_groups=5)
                    grouped_norm = self._cap_normalize_themes(grouped, cap=5)
                    if grouped_norm:
                        llm_themes = grouped_norm
                model_path = llm_result.model_path
                model_used = llm_result.model_used
            except Exception as e:
                logger.warning("Weekly pulse LLM generate failed (themes/summary): %s", e, exc_info=True)
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

        if llm_enabled and total >= 10 and hasattr(self._llm, "judge_weekly_pulse"):
            try:
                llm_judge = self._llm.judge_weekly_pulse(summary, action_items, llm_themes or deterministic_themes)
                judge_score = float(llm_judge.overall_score)
                judge_metrics = dict(llm_judge.metrics or {})
                judge_rationale = str(llm_judge.rationale or "")
            except Exception as e:
                logger.warning("LLM judge scoring failed: %s", e)

        # LLM themes are the only themes shared for email/voice downstream use.
        themes = llm_themes
        primary = themes if themes else deterministic_themes
        top_themes = sorted(primary, key=lambda x: -int(x.get("count", 0)))[:3]
        user_quotes = self._quotes.extract(annotated, k=3) if total >= 10 else []
        review_sentiment_updates = [
            {"review_id": str(r["review_id"]), "sentiment": str(r["sentiment"])}
            for r in annotated
            if r.get("review_id") and r.get("sentiment")
        ]

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
            "top_themes": top_themes,
            "user_quotes": user_quotes,
            "llm_summary_text": llm_summary_text,
            "deterministic_summary_text": deterministic_summary,
            "model_path": model_path,
            "model_used": model_used,
            "deterministic_algorithm": "rule-based sentiment + frequency theme extraction + keyword WoW",
            "generated_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "judge": verdict,
            "judge_overall_score": judge_score,
            "judge_metrics": judge_metrics,
            "judge_rationale": judge_rationale,
            "keywords": keywords,
            "review_sentiment_updates": review_sentiment_updates,
        }
        return payload

    @staticmethod
    def _cap_normalize_themes(rows: list[dict], cap: int = 5) -> list[dict]:
        out: list[dict] = []
        for t in (rows or [])[:cap]:
            try:
                c = int(t.get("count", 0))
            except (TypeError, ValueError):
                c = 0
            sent = str(t.get("sentiment", "neutral") or "neutral").strip().lower()
            if sent not in ("positive", "neutral", "negative", "mixed"):
                sent = "neutral"
            out.append(
                {
                    "theme": str(t.get("theme", "")).strip(),
                    "count": c,
                    "sentiment": sent,
                }
            )
        return out

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
        lead_theme = deterministic_themes[0]["theme"] if deterministic_themes else "Uncategorized mentions (keyword-free)"
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
