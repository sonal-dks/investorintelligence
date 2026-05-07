"""High-level orchestration for refresh + query.

Composes ChunkingService, EmbeddingService, ChromaService, LexicalIndex,
EntityResolver, and RetrievalService into the two flows the rest of the app
cares about: ``refresh()`` and ``query()``.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Sequence

from ..models.schemas import RefreshResponse
from .chroma_service import ChromaService
from .chunking_service import chunk_fee_explainer_rows, chunk_funds
from .embedding_service import EmbeddingService
from .entity_resolver import EntityResolver, FundEntity
from .lexical_index import LexicalIndex
from .retrieval_service import RetrievalService
from .supabase_reader import fetch_fee_explainer_rows, fetch_latest_funds

logger = logging.getLogger(__name__)


class RAGPipeline:
    def __init__(
        self,
        chroma: ChromaService | None = None,
        embedder: EmbeddingService | None = None,
    ) -> None:
        self._chroma = chroma or ChromaService()
        self._embedder = embedder or EmbeddingService()
        self._lexical: LexicalIndex | None = None
        self._resolver: EntityResolver | None = None
        self._refresh_lock = threading.Lock()
        self._collection_built = False

    def _rebuild_in_memory_indexes(self, funds: Sequence[dict]) -> None:
        docs = self._chroma.all_documents()
        self._lexical = LexicalIndex(docs)
        self._resolver = EntityResolver(
            [
                FundEntity(fund_slug=f["fund_slug"], fund_name=f["fund_name"])
                for f in funds
                if f.get("fund_slug") and f.get("fund_name")
            ]
        )
        self._collection_built = True

    def _bootstrap_from_existing_collection(self) -> None:
        """If process restarts, rebuild BM25 + resolver from persisted Chroma."""

        docs = self._chroma.all_documents()
        if not docs:
            self._lexical = LexicalIndex([])
            self._resolver = EntityResolver([])
            return
        self._lexical = LexicalIndex(docs)
        slugs_seen: set[str] = set()
        entities: list[FundEntity] = []
        for d in docs:
            meta = d.get("metadata") or {}
            if meta.get("corpus") == "fee_explainer":
                continue
            slug = meta.get("fund_slug")
            if not slug or slug in slugs_seen:
                continue
            slugs_seen.add(slug)
            display = " ".join(part.capitalize() for part in slug.replace("-", " ").split())
            entities.append(FundEntity(fund_slug=slug, fund_name=display))
        self._resolver = EntityResolver(entities)
        self._collection_built = True

    def ensure_ready(self) -> None:
        if self._collection_built:
            return
        self._bootstrap_from_existing_collection()

    def get_retrieval(self) -> RetrievalService:
        self.ensure_ready()
        assert self._lexical is not None and self._resolver is not None
        return RetrievalService(
            chroma=self._chroma,
            embedder=self._embedder,
            lexical=self._lexical,
            resolver=self._resolver,
        )

    def refresh(self, funds: Sequence[dict] | None = None) -> RefreshResponse:
        if not self._refresh_lock.acquire(blocking=False):
            raise RuntimeError("refresh already in progress")
        try:
            started = time.time()
            errors: list[str] = []
            if funds is None:
                try:
                    funds = fetch_latest_funds()
                except Exception as exc:  # noqa: BLE001
                    logger.exception("supabase_fetch_failed")
                    return RefreshResponse(
                        status="failed",
                        funds_processed=0,
                        chunks_generated=0,
                        embeddings_time_ms=0,
                        collection_size=self._chroma.collection_size(),
                        embedding_model_used="",
                        errors=[f"supabase_fetch_failed: {exc}"],
                    )

            mf_chunks, skipped = chunk_funds(funds)
            fee_rows = fetch_fee_explainer_rows()
            fee_chunks, _fee_skipped = chunk_fee_explainer_rows(fee_rows)
            chunks = list(mf_chunks) + list(fee_chunks)
            if not chunks:
                return RefreshResponse(
                    status="failed",
                    funds_processed=len(funds),
                    chunks_generated=0,
                    embeddings_time_ms=0,
                    collection_size=self._chroma.collection_size(),
                    embedding_model_used="",
                    skipped_funds=skipped,
                    errors=["no_chunks_generated"],
                )

            embed_started = time.time()
            try:
                vectors = self._embedder.encode_passages([c.text for c in chunks])
            except Exception as exc:  # noqa: BLE001
                logger.exception("embedding_failed")
                return RefreshResponse(
                    status="failed",
                    funds_processed=len(funds),
                    chunks_generated=len(chunks),
                    embeddings_time_ms=int((time.time() - embed_started) * 1000),
                    collection_size=self._chroma.collection_size(),
                    embedding_model_used="",
                    skipped_funds=skipped,
                    errors=[f"embedding_failed: {exc}"],
                )
            embed_ms = int((time.time() - embed_started) * 1000)

            collection = self._chroma.reset_collection()
            self._chroma.upsert_chunks(
                chunks=chunks,
                embeddings=[vec.tolist() for vec in vectors],
                collection=collection,
            )

            self._rebuild_in_memory_indexes(funds)

            response = RefreshResponse(
                status="success" if not errors else "partial",
                funds_processed=len(funds),
                chunks_generated=len(chunks),
                embeddings_time_ms=embed_ms,
                collection_size=self._chroma.collection_size(),
                embedding_model_used=self._embedder.model_name,
                skipped_funds=skipped,
                errors=errors,
            )
            logger.info(
                "refresh_complete",
                extra={
                    "funds_processed": response.funds_processed,
                    "chunks_generated": response.chunks_generated,
                    "embed_ms": embed_ms,
                    "total_ms": int((time.time() - started) * 1000),
                    "model": response.embedding_model_used,
                },
            )
            return response
        finally:
            self._refresh_lock.release()
