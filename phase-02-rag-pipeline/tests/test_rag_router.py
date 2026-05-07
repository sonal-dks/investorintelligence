"""HTTP-layer tests using FastAPI's TestClient with an injected stub pipeline."""

from __future__ import annotations

from fastapi.testclient import TestClient

from backend.app import create_app
from backend.models.schemas import (
    ChunkMetadata,
    QueryResponse,
    RefreshResponse,
    RetrievalResult,
)
from backend.routers import rag_router


class _FakePipeline:
    class _FakeChroma:
        collection_name = "stub"

        def collection_size(self) -> int:
            return 7

    class _FakeEmbedder:
        _model = "loaded"
        model_name = "stub-embedder"

    def __init__(self) -> None:
        self._chroma = self._FakeChroma()
        self._embedder = self._FakeEmbedder()

    def ensure_ready(self) -> None: ...

    def get_retrieval(self):
        class _R:
            def query(self_inner, query: str, top_k: int, fund_filter):
                if len(query) < 3:
                    raise ValueError("query too short")
                return QueryResponse(
                    results=[
                        RetrievalResult(
                            text="Exit load for Mirae Asset Large Cap: 1% if redeemed within 1 year",
                            metadata=ChunkMetadata(
                                fund_slug="mirae-asset-large-cap-fund-direct-growth",
                                chunk_type="fact",
                                source_field="exit_load",
                                scraped_at="2026-05-07T00:00:00Z",
                            ),
                            score=0.92,
                        )
                    ],
                    query_time_ms=12,
                    resolved_fund_slug="mirae-asset-large-cap-fund-direct-growth",
                    used_dynamic_k=top_k,
                    embedding_model_used="stub-embedder",
                )

        return _R()

    def refresh(self):
        return RefreshResponse(
            status="success",
            funds_processed=30,
            chunks_generated=285,
            embeddings_time_ms=11200,
            collection_size=285,
            embedding_model_used="stub-embedder",
        )


def _client() -> TestClient:
    rag_router.set_pipeline(_FakePipeline())
    return TestClient(create_app())


def test_health_endpoint():
    client = _client()
    res = client.get("/api/rag/health")
    assert res.status_code == 200
    body = res.json()
    assert body["collection_size"] == 7
    assert body["collection_name"] == "stub"


def test_query_happy_path():
    client = _client()
    res = client.post(
        "/api/rag/query",
        json={"query": "What is the exit load of Mirae Asset Large Cap?", "top_k": 5},
    )
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["results"]
    assert "1%" in body["results"][0]["text"]
    assert body["resolved_fund_slug"] == "mirae-asset-large-cap-fund-direct-growth"


def test_query_short_string_400():
    client = _client()
    res = client.post("/api/rag/query", json={"query": "ab"})
    assert res.status_code == 422  # caught by pydantic min_length


def test_refresh_endpoint():
    client = _client()
    res = client.post("/api/rag/refresh")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "success"
    assert body["funds_processed"] == 30
