from __future__ import annotations

import re
from collections import Counter

STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "this",
    "that",
    "have",
    "from",
    "your",
    "very",
    "app",
}


class KeywordTracker:
    def _tokenize(self, text: str) -> list[str]:
        tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_-]{2,}", text.lower())
        return [t for t in tokens if t not in STOPWORDS]

    def compute(
        self,
        reviews: list[dict],
        previous_counts: dict[str, int] | None = None,
        limit: int = 15,
    ) -> list[dict]:
        previous_counts = previous_counts or {}
        counter: Counter[str] = Counter()
        for review in reviews:
            counter.update(self._tokenize(str(review.get("review_text", ""))))

        rows: list[dict] = []
        for keyword, mentions in counter.most_common(limit):
            prev = previous_counts.get(keyword, 0)
            wow_change = 100.0 if prev == 0 and mentions > 0 else 0.0
            if prev > 0:
                wow_change = ((mentions - prev) / prev) * 100.0
            trend = "up" if wow_change > 0 else "down" if wow_change < 0 else "flat"
            rows.append(
                {
                    "keyword": keyword,
                    "mention_count": mentions,
                    "wow_change_pct": round(wow_change, 2),
                    "trend": trend,
                }
            )
        return rows
