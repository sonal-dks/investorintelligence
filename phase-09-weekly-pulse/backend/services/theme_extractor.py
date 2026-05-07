from __future__ import annotations

from collections import Counter


class ThemeExtractor:
    """Lightweight deterministic fallback theme extraction."""

    _THEME_MAP: dict[str, str] = {
        "slow": "App Performance",
        "lag": "App Performance",
        "crash": "App Stability",
        "bug": "App Stability",
        "sip": "SIP Workflow",
        "portfolio": "Portfolio Experience",
        "dark mode": "Dark Mode",
        "ui": "UI/UX",
        "support": "Support Experience",
    }

    def extract(self, reviews: list[dict], limit: int = 5) -> list[dict]:
        counts: Counter[str] = Counter()
        sentiment_by_theme: dict[str, Counter[str]] = {}
        for review in reviews:
            text = str(review.get("review_text", "")).lower()
            sentiment = str(review.get("sentiment", "neutral"))
            matched = set()
            for token, theme in self._THEME_MAP.items():
                if token in text:
                    matched.add(theme)
            if not matched:
                matched.add("General Product Feedback")
            for theme in matched:
                counts[theme] += 1
                sentiment_by_theme.setdefault(theme, Counter())[sentiment] += 1

        top = counts.most_common(limit)
        result: list[dict] = []
        for theme, count in top:
            dominant_sentiment = sentiment_by_theme[theme].most_common(1)[0][0]
            result.append(
                {
                    "theme": theme,
                    "count": count,
                    "sentiment": dominant_sentiment,
                }
            )
        return result
