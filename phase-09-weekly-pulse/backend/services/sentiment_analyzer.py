from __future__ import annotations

from typing import Literal

Sentiment = Literal["positive", "neutral", "negative"]


class SentimentAnalyzer:
    """Rule-first sentiment classifier aligned to phase criteria."""

    @staticmethod
    def classify_rating(rating: int) -> Sentiment:
        if rating >= 4:
            return "positive"
        if rating == 3:
            return "neutral"
        return "negative"

    def annotate(self, reviews: list[dict]) -> list[dict]:
        out: list[dict] = []
        for review in reviews:
            copied = dict(review)
            copied["sentiment"] = self.classify_rating(int(copied.get("rating", 0)))
            out.append(copied)
        return out
