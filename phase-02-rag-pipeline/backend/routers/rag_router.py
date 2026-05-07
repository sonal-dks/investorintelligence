"""HTTP layer for the Phase 02 RAG pipeline.

Per LLD §API Contracts:
  POST /api/rag/query   — top-k retrieval (used internally by Phase 05)
  POST /api/rag/refresh — full rebuild from Supabase
  GET  /api/rag/health  — collection size + embedding model used
"""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException

from ..models.schemas import QueryRequest, QueryResponse, RefreshResponse
from ..services.rag_pipeline import RAGPipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/rag", tags=["rag"])

_pipeline: RAGPipeline | None = None


def get_pipeline() -> RAGPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = RAGPipeline()
    return _pipeline


def set_pipeline(pipeline: RAGPipeline) -> None:
    """Test hook for injecting a pipeline with a stub embedder/Chroma."""

    global _pipeline
    _pipeline = pipeline


@router.post("/query", response_model=QueryResponse)
def query(request: QueryRequest) -> QueryResponse:
    pipeline = get_pipeline()
    try:
        retrieval = pipeline.get_retrieval()
        try:
            return retrieval.query(
                query=request.query,
                top_k=request.top_k,
                fund_filter=request.fund_filter,
                corpus_filter=request.corpus_filter,
            )
        except TypeError:
            # Backward compatibility for older retrieval stubs/signatures.
            return retrieval.query(
                query=request.query,
                top_k=request.top_k,
                fund_filter=request.fund_filter,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("query_failed")
        raise HTTPException(status_code=500, detail=f"retrieval failed: {exc}") from exc


@router.post("/refresh", response_model=RefreshResponse)
def refresh() -> RefreshResponse:
    pipeline = get_pipeline()
    try:
        return pipeline.refresh()
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        logger.exception("refresh_failed")
        raise HTTPException(status_code=500, detail=f"refresh failed: {exc}") from exc


@router.get("/health")
def health() -> dict:
    pipeline = get_pipeline()
    pipeline.ensure_ready()
    return {
        "collection_size": pipeline._chroma.collection_size(),
        "collection_name": pipeline._chroma.collection_name,
        "embedding_model": pipeline._embedder.model_name
        if pipeline._embedder._model is not None
        else None,
    }
