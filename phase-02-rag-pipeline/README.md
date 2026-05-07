# Phase 02 — RAG Pipeline (Embeddings + Vector Store)

Reads the latest mutual-fund rows from Supabase (populated by Phase 01),
chunks them into hybrid (fact + description) passages, embeds with
`BAAI/bge-large-en-v1.5` (with `all-MiniLM-L6-v2` fallback), and serves
hybrid retrieval (vector + BM25 + entity resolution + dynamic-k) over a
persistent ChromaDB collection.

See `Docs/Architecture/architecture.md` §Phase 02, `HLD.md` §Phase 02, and
`LLD.md` §Phase 02 for the full architecture.

## Layout

```
phase-02-rag-pipeline/
├── backend/
│   ├── app.py                       FastAPI app (POST /api/rag/{query,refresh}, GET /api/rag/health)
│   ├── config/settings.py           Env-driven config
│   ├── models/schemas.py            Pydantic schemas
│   ├── routers/rag_router.py        HTTP layer
│   └── services/
│       ├── chunking_service.py      Hybrid chunks + rule extractors
│       ├── embedding_service.py     BGE primary + MiniLM fallback (lazy)
│       ├── chroma_service.py        Persistent ChromaDB wrapper
│       ├── lexical_index.py         BM25 sidecar
│       ├── entity_resolver.py       rapidfuzz fund canonicalization
│       ├── supabase_reader.py       Latest-per-fund_slug reader
│       ├── retrieval_service.py     Hybrid retrieval + RRF + dynamic-k
│       └── rag_pipeline.py          End-to-end orchestrator
├── tests/                           35 unit + integration tests
├── expected_outputs/                Reference JSON fixtures + benchmark
├── run_refresh.py                   CLI: rebuild collection from Supabase
├── run_query.py                     CLI: run a single query
├── run_benchmark.py                 CLI: 20-query precision benchmark
├── requirements.txt
└── .env                             SUPABASE_*, CHROMA_*, RAG_* knobs
```

## Setup

```bash
# From the phase-02-rag-pipeline/ directory
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Environment variables (see `.env`):

| Variable | Purpose | Default |
|----------|---------|---------|
| `SUPABASE_URL` / `SUPABASE_SERVICE_ROLE_KEY` | Read access to `mutual_fund_data` | required |
| `CHROMA_PERSIST_DIR` | Where ChromaDB writes its files | `./chroma_data` |
| `EMBEDDING_MODEL` | Primary sentence-transformer | `BAAI/bge-large-en-v1.5` |
| `EMBEDDING_FALLBACK_MODEL` | Used if primary fails to load | `sentence-transformers/all-MiniLM-L6-v2` |
| `CHROMA_COLLECTION_NAME` | Collection name | `mutual_fund_knowledge` |
| `RAG_DEFAULT_TOP_K` | Default `top_k` when caller doesn't pass one | 5 |
| `RAG_DYNAMIC_K_MIN` / `RAG_DYNAMIC_K_MAX` | Lower / upper bound for dynamic-k | 3 / 12 |
| `RAG_SCORE_THRESHOLD` | Min cosine similarity for vector-only hits | 0.3 |
| `RAG_ENTITY_FUZZ_THRESHOLD` | Min rapidfuzz score for fund resolution | 70 |

## Run

```bash
# 1) Build / rebuild the collection from Supabase
python run_refresh.py

# 2) Ad-hoc query
python run_query.py "What is the exit load of Mirae Asset Large Cap?" --top-k 5

# 3) Precision benchmark (20 queries, success threshold ≥ 80%)
python run_benchmark.py

# 4) Local FastAPI server
uvicorn backend.app:app --reload --port 8002
# then:  curl http://localhost:8002/api/rag/health
```

## Tests

```bash
pytest tests/ -v
# 35 tests, ~1s; uses stub embedder/Chroma so no model download is needed.

ruff check backend tests run_*.py
```

## Live verification artifacts

`expected_outputs/benchmark_result.json` contains the most recent live
benchmark output (top-3 precision, per-query results). Re-run
`run_benchmark.py --json > expected_outputs/benchmark_result.json` after any
chunker/retrieval change.
