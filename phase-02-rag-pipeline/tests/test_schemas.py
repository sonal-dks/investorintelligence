"""Schema-level edge cases (input validation per LLD §Validation and Guardrails)."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from backend.models.schemas import Chunk, ChunkMetadata, QueryRequest


def test_query_request_min_length_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(query="ab")


def test_query_request_max_length_rejected():
    with pytest.raises(ValidationError):
        QueryRequest(query="a" * 501)


def test_top_k_bounds_enforced():
    with pytest.raises(ValidationError):
        QueryRequest(query="exit load mirae", top_k=0)
    with pytest.raises(ValidationError):
        QueryRequest(query="exit load mirae", top_k=21)


def test_chunk_minimum_length_validated():
    meta = ChunkMetadata(
        fund_slug="x", chunk_type="fact", source_field="nav", scraped_at="2026-05-07T00:00:00Z"
    )
    with pytest.raises(ValidationError):
        Chunk(id="x::fact::nav", text="too short", metadata=meta)
