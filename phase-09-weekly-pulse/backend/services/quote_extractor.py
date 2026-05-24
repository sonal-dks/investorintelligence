from __future__ import annotations

import re


class QuoteExtractor:
    """Pick verbatim excerpts from review text (no LLM) for auditability."""

    _DIGIT_RUN = re.compile(r"\d{10,}")

    def extract(self, reviews: list[dict], k: int = 3, max_len: int = 200, min_len: int = 20) -> list[str]:
        quotes: list[str] = []
        used_i: set[int] = set()
        for i, review in enumerate(reviews):
            if len(quotes) >= k:
                break
            if i in used_i:
                continue
            text = str(review.get("review_text", "")).strip()
            if len(text) < min_len:
                continue
            if self._unsafe_for_quote(text):
                continue
            excerpt = self._clip(text, max_len=max_len, min_len=min_len)
            if not excerpt or self._unsafe_for_quote(excerpt):
                continue
            used_i.add(i)
            quotes.append(excerpt)
        return quotes

    def _unsafe_for_quote(self, text: str) -> bool:
        if "@" in text:
            return True
        return bool(self._DIGIT_RUN.search(text))

    def _clip(self, text: str, max_len: int, min_len: int) -> str:
        if len(text) <= max_len:
            return text if len(text) >= min_len else ""
        # Prefer first sentence if it fits length bounds.
        for sep in (". ", "! ", "? "):
            idx = text.find(sep)
            if idx != -1:
                sent = text[: idx + 1].strip()
                if min_len <= len(sent) <= max_len:
                    return sent
                if len(sent) > max_len:
                    break
        prefix = text[:max_len]
        if " " in prefix:
            prefix = prefix.rsplit(" ", 1)[0]
        return prefix.strip() if len(prefix.strip()) >= min_len else ""
