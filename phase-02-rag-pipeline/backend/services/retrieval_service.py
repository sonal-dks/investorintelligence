"""RetrievalService — hybrid (vector + BM25) retrieval with entity resolution.

Implements Addendum A2 steps #1–#4 (query normalization, entity resolver,
hybrid retrieval, dynamic-k).  Cross-encoder reranking (#5) and conversation
memory (#6/#7) are intentionally deferred: they belong to Phase 05's chat
layer, not the corpus-side retrieval API.

Hybrid fusion uses **Reciprocal Rank Fusion** (Cormack et al. 2009):

    rrf_score(d) = Σ over rankers  1 / (k_const + rank_d)

with k_const = 60.  RRF tolerates the very different score scales of cosine
similarity (0–1) and BM25 (0–∞) and is a strong default for this size of
collection (~285 docs).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import Sequence

from ..config.settings import SETTINGS
from ..models.schemas import ChunkMetadata, QueryResponse, RetrievalResult
from .chroma_service import ChromaService
from .embedding_service import EmbeddingService
from .entity_resolver import EntityResolver, FundEntity
from .lexical_index import LexicalIndex

logger = logging.getLogger(__name__)

RRF_K = 60


def _meta_corpus_ok(metadata: dict, corpus_filter: str | None) -> bool:
    if corpus_filter is None:
        return True
    c = metadata.get("corpus") or "mutual_fund"
    return c == corpus_filter


def _vector_where_clause(fund_filter: str | None, corpus_filter: str | None) -> dict | None:
    """Chroma metadata filter for the vector arm.

    ``fee_explainer`` rows always have ``corpus`` set. Legacy mutual-fund chunks
    may omit ``corpus``; those are treated as mutual fund via post-filtering
    when ``corpus_filter == \"mutual_fund\"``.
    """

    if corpus_filter == "fee_explainer":
        return {"corpus": "fee_explainer"}
    if fund_filter:
        return {"fund_slug": fund_filter}
    return None


@dataclass
class _Candidate:
    id: str
    text: str
    metadata: dict
    vector_score: float = 0.0
    lexical_score: float = 0.0
    rrf_score: float = 0.0


class RetrievalService:
    def __init__(
        self,
        chroma: ChromaService,
        embedder: EmbeddingService,
        lexical: LexicalIndex,
        resolver: EntityResolver,
    ) -> None:
        self._chroma = chroma
        self._embedder = embedder
        self._lexical = lexical
        self._resolver = resolver

    def query(
        self,
        query: str,
        top_k: int | None = None,
        fund_filter: str | None = None,
        corpus_filter: str | None = None,
    ) -> QueryResponse:
        started = time.time()
        cleaned = (query or "").strip()
        if len(cleaned) < 3:
            raise ValueError("query must be at least 3 characters")
        if len(cleaned) > 500:
            cleaned = cleaned[:500]

        requested_k = top_k or SETTINGS.default_top_k
        requested_k = max(SETTINGS.dynamic_k_min, min(SETTINGS.dynamic_k_max, requested_k))

        resolved_slug = fund_filter
        if resolved_slug is None:
            resolved = self._resolver.resolve(cleaned)
            if resolved is not None:
                entity, _ = resolved
                resolved_slug = entity.fund_slug

        # Fee explainer corpus is not scoped by fund_slug; ignore entity resolution.
        if corpus_filter == "fee_explainer":
            resolved_slug = None

        # 1) Vector arm — fetch a candidate pool (>= top_k) so RRF has options.
        pool_size = max(requested_k * 3, 15)
        query_vec = self._embedder.encode_query(cleaned)
        vec_where = _vector_where_clause(resolved_slug, corpus_filter)
        vector_hits = self._chroma.query(query_vec.tolist(), top_k=pool_size, where=vec_where)
        if corpus_filter == "mutual_fund":
            vector_hits = [
                h for h in vector_hits if _meta_corpus_ok(h.get("metadata") or {}, "mutual_fund")
            ]

        # 2) Lexical arm — fund_filter applied post-hoc since BM25 is in-memory.
        lexical_hits_raw = self._lexical.search(cleaned, top_k=pool_size)
        if resolved_slug and corpus_filter != "fee_explainer":
            lexical_hits_raw = [
                h for h in lexical_hits_raw if (h.get("metadata") or {}).get("fund_slug") == resolved_slug
            ]
        lexical_hits = [
            h for h in lexical_hits_raw if _meta_corpus_ok(h.get("metadata") or {}, corpus_filter)
        ]

        # 3) RRF fusion
        candidates: dict[str, _Candidate] = {}

        for rank, hit in enumerate(vector_hits):
            cid = hit["id"]
            cand = candidates.setdefault(
                cid,
                _Candidate(id=cid, text=hit["text"], metadata=hit["metadata"]),
            )
            cand.vector_score = float(hit["score"])
            cand.rrf_score += 1.0 / (RRF_K + rank + 1)

        for rank, hit in enumerate(lexical_hits):
            cid = hit["id"]
            cand = candidates.setdefault(
                cid,
                _Candidate(id=cid, text=hit["text"], metadata=hit["metadata"]),
            )
            cand.lexical_score = float(hit["score"])
            cand.rrf_score += 1.0 / (RRF_K + rank + 1)

        ranked = sorted(candidates.values(), key=lambda c: c.rrf_score, reverse=True)

        # 4) Dynamic-k: return min top_k if best vector_score is high enough,
        #    otherwise expand until we cover SETTINGS.dynamic_k_max or the pool.
        best_vec_score = ranked[0].vector_score if ranked else 0.0
        if best_vec_score >= 0.7:
            effective_k = max(SETTINGS.dynamic_k_min, requested_k)
        elif best_vec_score >= 0.4:
            effective_k = min(SETTINGS.dynamic_k_max, max(requested_k, SETTINGS.default_top_k + 2))
        else:
            effective_k = SETTINGS.dynamic_k_max
        effective_k = min(effective_k, len(ranked)) if ranked else effective_k

        final = ranked[:effective_k]

        results: list[RetrievalResult] = []
        for cand in final:
            score = cand.vector_score if cand.vector_score > 0 else cand.rrf_score
            if score < SETTINGS.score_threshold and cand.lexical_score == 0:
                continue
            try:
                meta = ChunkMetadata(**cand.metadata)
            except Exception as exc:  # noqa: BLE001
                logger.warning(
                    "metadata_parse_failed",
                    extra={"id": cand.id, "metadata": cand.metadata, "error": str(exc)},
                )
                continue
            results.append(
                RetrievalResult(text=cand.text, metadata=meta, score=round(score, 4))
            )

        elapsed_ms = int((time.time() - started) * 1000)
        logger.info(
            "retrieval_complete",
            extra={
                "query": cleaned,
                "resolved_fund_slug": resolved_slug,
                "vector_hits": len(vector_hits),
                "lexical_hits": len(lexical_hits),
                "returned": len(results),
                "elapsed_ms": elapsed_ms,
                "best_vec_score": best_vec_score,
                "effective_k": effective_k,
            },
        )
        return QueryResponse(
            results=results,
            query_time_ms=elapsed_ms,
            resolved_fund_slug=resolved_slug,
            used_dynamic_k=effective_k,
            embedding_model_used=self._embedder.model_name,
        )


def build_resolver_from_funds(funds: Sequence[dict]) -> EntityResolver:
    entities = [
        FundEntity(fund_slug=f["fund_slug"], fund_name=f["fund_name"])
        for f in funds
        if f.get("fund_slug") and f.get("fund_name")
    ]
    return EntityResolver(entities)
