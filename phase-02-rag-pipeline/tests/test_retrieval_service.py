"""Unit tests for RetrievalService.

These tests use **stub** Chroma + embedder so they run in milliseconds without
the 2GB BGE download or a live ChromaDB on disk.  Live integration is exercised
by ``test_pipeline_e2e_live`` (skipped by default).
"""

from __future__ import annotations

from typing import Sequence

import numpy as np
import pytest

from backend.services.entity_resolver import EntityResolver, FundEntity
from backend.services.lexical_index import LexicalIndex
from backend.services.retrieval_service import RetrievalService


class _StubEmbedder:
    """Maps a small vocabulary of phrases to deterministic 4-dim vectors."""

    model_name = "stub-embedder"
    dim = 4
    _model = "loaded"

    _table = {
        "exit_load_mirae": np.array([1.0, 0.1, 0.0, 0.0], dtype=np.float32),
        "nav_mirae": np.array([0.1, 1.0, 0.0, 0.0], dtype=np.float32),
        "expense_parag": np.array([0.0, 0.1, 1.0, 0.0], dtype=np.float32),
        "exit_load_parag": np.array([0.0, 0.0, 0.1, 1.0], dtype=np.float32),
    }

    def encode_passages(self, texts: Sequence[str]) -> np.ndarray:
        return np.stack([self._encode(t) for t in texts])

    def encode_query(self, text: str) -> np.ndarray:
        return self._encode(text)

    def _encode(self, text: str) -> np.ndarray:
        text_l = text.lower()
        if "exit" in text_l and "mirae" in text_l:
            return self._table["exit_load_mirae"]
        if "nav" in text_l and "mirae" in text_l:
            return self._table["nav_mirae"]
        if "expense" in text_l and "parag" in text_l:
            return self._table["expense_parag"]
        if "exit" in text_l and "parag" in text_l:
            return self._table["exit_load_parag"]
        return np.array([0.25, 0.25, 0.25, 0.25], dtype=np.float32)


class _StubChroma:
    """In-memory cosine search over a fixed corpus (matches ChromaService API)."""

    collection_name = "stub"

    def __init__(self) -> None:
        self._docs = [
            {
                "id": "mirae::fact::exit_load",
                "text": "Exit load for Mirae Asset Large Cap: 1% if redeemed within 1 year",
                "metadata": {
                    "fund_slug": "mirae-asset-large-cap-fund-direct-growth",
                    "chunk_type": "fact",
                    "source_field": "exit_load",
                    "scraped_at": "2026-05-07T00:00:00Z",
                },
            },
            {
                "id": "mirae::fact::nav",
                "text": "NAV of Mirae Asset Large Cap: ₹105.43 as of 2026-05-06",
                "metadata": {
                    "fund_slug": "mirae-asset-large-cap-fund-direct-growth",
                    "chunk_type": "fact",
                    "source_field": "nav",
                    "scraped_at": "2026-05-07T00:00:00Z",
                },
            },
            {
                "id": "parag::fact::expense_ratio",
                "text": "Expense ratio of Parag Parikh Flexi Cap: 0.65%",
                "metadata": {
                    "fund_slug": "parag-parikh-flexi-cap-fund-direct-growth",
                    "chunk_type": "fact",
                    "source_field": "expense_ratio",
                    "scraped_at": "2026-05-07T00:00:00Z",
                },
            },
        ]
        self._vecs = {
            "mirae::fact::exit_load": np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float32),
            "mirae::fact::nav": np.array([0.0, 1.0, 0.0, 0.0], dtype=np.float32),
            "parag::fact::expense_ratio": np.array([0.0, 0.0, 1.0, 0.0], dtype=np.float32),
        }

    def all_documents(self) -> list[dict]:
        return list(self._docs)

    def collection_size(self) -> int:
        return len(self._docs)

    def query(self, embedding, top_k: int, where: dict | None = None) -> list[dict]:
        q = np.array(embedding, dtype=np.float32)
        q_norm = q / (np.linalg.norm(q) + 1e-9)
        out: list[dict] = []
        for doc in self._docs:
            if where and (doc["metadata"].get("fund_slug") != where.get("fund_slug")):
                continue
            v = self._vecs[doc["id"]]
            v_norm = v / (np.linalg.norm(v) + 1e-9)
            score = float(q_norm @ v_norm)
            out.append({**doc, "score": max(0.0, score)})
        out.sort(key=lambda d: d["score"], reverse=True)
        return out[:top_k]


@pytest.fixture()
def service() -> RetrievalService:
    chroma = _StubChroma()
    embedder = _StubEmbedder()
    lexical = LexicalIndex(chroma.all_documents())
    resolver = EntityResolver(
        [
            FundEntity(
                fund_slug="mirae-asset-large-cap-fund-direct-growth",
                fund_name="Mirae Asset Large Cap Fund Direct Growth",
            ),
            FundEntity(
                fund_slug="parag-parikh-flexi-cap-fund-direct-growth",
                fund_name="Parag Parikh Flexi Cap Fund Direct Growth",
            ),
        ]
    )
    return RetrievalService(chroma=chroma, embedder=embedder, lexical=lexical, resolver=resolver)


def test_query_too_short_raises(service):
    with pytest.raises(ValueError):
        service.query("ab")


def test_exit_load_query_returns_correct_chunk_first(service):
    response = service.query("What is the exit load of Mirae Asset Large Cap?")
    assert response.results, "no results"
    assert "1%" in response.results[0].text
    assert response.results[0].metadata.fund_slug == "mirae-asset-large-cap-fund-direct-growth"


def test_typo_query_resolves_to_correct_fund(service):
    response = service.query("tell query about mirae larg cap exit load")
    assert response.resolved_fund_slug == "mirae-asset-large-cap-fund-direct-growth"
    assert response.results
    assert all(
        r.metadata.fund_slug == "mirae-asset-large-cap-fund-direct-growth"
        for r in response.results
    )


def test_explicit_fund_filter_constrains_results(service):
    response = service.query(
        "expense ratio",
        fund_filter="parag-parikh-flexi-cap-fund-direct-growth",
    )
    for r in response.results:
        assert r.metadata.fund_slug == "parag-parikh-flexi-cap-fund-direct-growth"


def test_query_response_includes_diagnostics(service):
    response = service.query("Mirae Asset Large Cap NAV")
    assert response.embedding_model_used == "stub-embedder"
    assert response.used_dynamic_k >= 1
    assert response.query_time_ms >= 0


def test_long_query_is_truncated_not_rejected(service):
    long_q = "exit load mirae " * 200
    response = service.query(long_q)
    assert response.results
