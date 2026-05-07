# Phase 02: RAG Pipeline - Edge Cases and Success Criteria

## Detailed Edge Cases
- Input edge: chunk boundaries split critical fee phrases, malformed text includes HTML/script noise.
- Retrieval edge: vector-only top-k misses exact fee rule text, low-score chunks outrank exact lexical hits.
- Query edge: typo fund mention ("mirae larg cap"), shorthand aliases, mixed Hindi-English phrasing.
- Dependency edge: embedding model unavailable, vector index corruption, re-embedding run interrupted.
- Context edge: stale chunks after source refresh cause outdated responses.

## Success Criteria
- Hybrid retrieval (vector + lexical) is enabled and measurable in logs.
- Dynamic-k + reranking improves retrieval relevance on benchmark queries.
- Entity resolver maps typo/semantic fund mentions to canonical fund identity.
- Query "What is the exit load of Mirae Asset Large Cap?" retrieves chunk containing "1% if redeemed before 1 year".
- Index refresh invalidates stale chunks and serves latest scraped fund facts.

## Implementation Status (Phase 02 — completed May 2026)

### Edge Cases — Coverage
- [x] **Chunk boundaries split fee phrases** — `_extract_exit_load_rule()` regex extracts the active rule out of run-together Groww copy; verified on live data ("Exit load of 1% if redeemed within 1 year").
- [x] **HTML/script noise in source text** — only typed Supabase columns are read; long-text fields are filtered through dedicated rule extractors so glossary text never lands in a fact chunk.
- [x] **Vector-only top-k misses exact rule text** — `LexicalIndex` (BM25) sidecar runs in parallel with the vector arm.
- [x] **Low-score chunks outrank exact lexical hits** — Reciprocal Rank Fusion (`k_const=60`) blends both rankers; lexical-positive hits are kept even if their vector score is below `RAG_SCORE_THRESHOLD`.
- [x] **Typo fund mention** — `EntityResolver` (rapidfuzz `token_set_ratio` over a stop-word-stripped haystack) resolves "mirae larg cap" → `mirae-asset-large-cap-fund-direct-growth`.
- [x] **Shorthand aliases** — covered in `tests/test_entity_resolver.py::test_shorthand_resolves_to_elss`.
- [x] **Mixed Hindi-English phrasing** — Hindi function words (`kya`, `hai`, `ka`, …) added to the resolver's stop-word list; covered in `tests/test_entity_resolver.py::test_mixed_language_query_still_resolves`.
- [x] **Embedding model unavailable** — `EmbeddingService` falls back from `BAAI/bge-large-en-v1.5` to `sentence-transformers/all-MiniLM-L6-v2` and reports the actual model in every response.
- [x] **Vector index corruption** — refresh is delete-and-recreate; ChromaDB is rebuildable from Supabase (Postgres is the source of truth).
- [x] **Re-embedding run interrupted** — non-blocking `threading.Lock` (returns 409 on concurrent refresh) prevents corruption; the next refresh recreates the collection cleanly.
- [x] **Stale chunks after source refresh** — `RAGPipeline.refresh()` clears the collection and rebuilds the BM25 + EntityResolver indexes from the new corpus.

### Success Criteria — Verification
- [x] **Hybrid retrieval enabled & measurable** — `RetrievalService` logs `vector_hits`, `lexical_hits`, `effective_k`, `best_vec_score` per query.
- [x] **Dynamic-k + reranking** — k widens to `RAG_DYNAMIC_K_MAX` (12) when best vector score < 0.4; RRF reranks across both arms.
- [x] **Entity resolver maps fuzzy mentions** — verified across exact, typo, shorthand, mixed-language test cases.
- [x] **Mandatory query "What is the exit load of Mirae Asset Large Cap?"** — top-1 result contains "Exit load of 1% if redeemed within 1 year" (live verification, score 0.857).
- [x] **Index refresh invalidates stale chunks** — collection is dropped and recreated; live refresh: 30 funds → 262 chunks in 17.5s.
- [x] **20-query precision benchmark** — 19/20 passed, **top-3 precision 95%** (threshold ≥ 80%).
