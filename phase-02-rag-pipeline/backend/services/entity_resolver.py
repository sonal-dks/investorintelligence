"""EntityResolver — maps fuzzy / shorthand fund mentions to canonical fund_slug.

Implements Addendum A2 step 2 ("Entity resolver: 'mirae larg cap' →
'Mirae Asset Large Cap Fund Direct Growth'") using rapidfuzz on a list of
known funds pulled from Supabase.

The resolver is deliberately conservative: if the best match score is below the
configured fuzz threshold, ``None`` is returned and the caller falls back to
unfiltered hybrid retrieval.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable

from rapidfuzz import fuzz, process

from ..config.settings import SETTINGS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class FundEntity:
    fund_slug: str
    fund_name: str

    @property
    def haystack(self) -> str:
        slug_words = self.fund_slug.replace("-", " ")
        return f"{self.fund_name} {slug_words}"

    @property
    def stripped_haystack(self) -> str:
        """Identifying tokens only (stopwords removed).  Used by the resolver."""

        return _strip_stopwords(self.haystack)


# Words that don't help identify which fund a query is about.
# Retrieval/metric vocabulary stays here so they don't drag fund-name fuzz scores
# down (e.g., "exit load mirae" should resolve like "mirae" alone does).
_STOPWORDS = {
    # English function words
    "a", "an", "of", "the", "in", "for", "what", "is", "are", "be", "do",
    "to", "on", "with", "from", "about", "tell", "me", "show", "explain",
    "this", "that", "those", "these", "please", "kindly", "any",
    # Hindi function words (transliterated, common in Indian English queries)
    "kya", "hai", "ka", "ki", "ke", "ko", "ne", "se", "mein", "main", "tum",
    "kar", "karte", "kaise", "kab", "kyun",
    # Generic mutual-fund vocabulary that all funds share
    "fund", "funds", "mutual", "direct", "regular", "growth", "plan", "scheme",
    "asset", "management",
    # Retrieval vocabulary (these are the *question* terms, not the *fund* terms)
    "nav", "exit", "load", "expense", "ratio", "return", "returns", "sip",
    "minimum", "min", "risk", "level", "tax", "aum", "category", "query",
    "value", "price", "performance",
}


def _strip_stopwords(text: str) -> str:
    tokens = re.findall(r"[a-zA-Z0-9]+", text.lower())
    keep = [t for t in tokens if t not in _STOPWORDS]
    return " ".join(keep) if keep else text.lower()


class EntityResolver:
    def __init__(self, funds: Iterable[FundEntity], fuzz_threshold: int | None = None) -> None:
        self._funds: list[FundEntity] = list(funds)
        self._threshold = fuzz_threshold or SETTINGS.entity_fuzz_threshold
        # Keyed on the stripped haystack — fund-identifying tokens only.
        self._lookup: dict[str, FundEntity] = {}
        for f in self._funds:
            key = f.stripped_haystack or f.haystack
            self._lookup.setdefault(key, f)

    @property
    def size(self) -> int:
        return len(self._funds)

    def resolve(self, query: str) -> tuple[FundEntity, int] | None:
        if not self._funds:
            return None
        normalized = _strip_stopwords(query)
        if not normalized.strip():
            return None
        match = process.extractOne(
            normalized,
            list(self._lookup.keys()),
            scorer=fuzz.token_set_ratio,
            score_cutoff=self._threshold,
        )
        if match is None:
            return None
        haystack, score, _ = match
        entity = self._lookup[haystack]
        logger.info(
            "entity_resolved",
            extra={
                "query": query,
                "fund_slug": entity.fund_slug,
                "score": score,
            },
        )
        return entity, int(score)
