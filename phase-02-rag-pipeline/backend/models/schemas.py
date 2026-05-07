"""Pydantic schemas for the RAG pipeline.

The shapes mirror the LLD §"Data Model Details" and the JSON contracts in
`Docs/Architecture/LLD.md` (Phase 02 §"Expected Outputs").
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator

ChunkType = Literal["fact", "description"]
CorpusType = Literal["mutual_fund", "fee_explainer"]

# Sentinel slug for fee-explainer chunks (not a real fund; entity resolver ignores it).
FEE_EXPLAINER_CORPUS_SLUG = "__fee_explainer__"


class ChunkMetadata(BaseModel):
    """Metadata stored on each Chroma document.

    ``corpus`` scopes retrieval (mutual fund facts vs fee explainer). Legacy
    chunks without ``corpus`` are treated as ``mutual_fund`` at query time.
    """

    fund_slug: str
    chunk_type: ChunkType
    source_field: str
    scraped_at: str
    corpus: CorpusType = "mutual_fund"
    fee_type: str | None = None
    source_url: str | None = None


class Chunk(BaseModel):
    """One embeddable passage built from a fund row."""

    id: str
    text: str
    metadata: ChunkMetadata

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        cleaned = v.strip()
        if len(cleaned) < 10:
            raise ValueError("chunk text must be >=10 chars")
        return cleaned


class RetrievalResult(BaseModel):
    text: str
    metadata: ChunkMetadata
    score: float


class QueryRequest(BaseModel):
    query: str = Field(min_length=3, max_length=500)
    top_k: int = Field(default=5, ge=1, le=20)
    fund_filter: Optional[str] = None  # canonical fund_slug to scope search
    corpus_filter: Optional[CorpusType] = None  # restrict to mutual_fund or fee_explainer


class QueryResponse(BaseModel):
    results: list[RetrievalResult]
    query_time_ms: int
    resolved_fund_slug: Optional[str] = None
    used_dynamic_k: int
    embedding_model_used: str


class RefreshResponse(BaseModel):
    status: Literal["success", "partial", "failed"]
    funds_processed: int
    chunks_generated: int
    embeddings_time_ms: int
    collection_size: int
    embedding_model_used: str
    skipped_funds: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
