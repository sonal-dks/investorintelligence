"""BM25 lexical index — pure-Python sidecar for hybrid retrieval.

The vector store handles semantics; BM25 handles exact phrase / fee-rule terms
("1% if redeemed before 1 year", "Direct Plan", "ELSS", etc.) where lexical
overlap matters more than embedding similarity.  Per Addendum A2 step 3:
"Hybrid retrieval (vector similarity + lexical/BM25 on key fields ...)".
"""

from __future__ import annotations

import re
from typing import Sequence

from rank_bm25 import BM25Okapi

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall((text or "").lower())


class LexicalIndex:
    def __init__(self, documents: Sequence[dict]) -> None:
        """``documents`` is a list of {"id", "text", "metadata"} dicts."""

        self._docs = list(documents)
        if self._docs:
            self._bm25 = BM25Okapi([tokenize(d["text"]) for d in self._docs])
        else:
            self._bm25 = None

    @property
    def size(self) -> int:
        return len(self._docs)

    def search(self, query: str, top_k: int) -> list[dict]:
        if self._bm25 is None or not self._docs or top_k <= 0:
            return []
        scores = self._bm25.get_scores(tokenize(query))
        if scores.size == 0:
            return []
        top_idx = scores.argsort()[::-1][:top_k]
        results: list[dict] = []
        for idx in top_idx:
            score = float(scores[idx])
            if score <= 0:
                continue
            doc = self._docs[idx]
            results.append(
                {
                    "id": doc["id"],
                    "text": doc["text"],
                    "metadata": doc["metadata"],
                    "score": score,
                }
            )
        return results
