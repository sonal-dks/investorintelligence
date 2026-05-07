# Phase 11 — Evaluation Suite

Implements continuous AI quality evaluation for:
- RAG faithfulness
- RAG relevance
- Safety/adversarial behavior
- UX constraints

## Run

```bash
cd phase-11-evaluation-suite
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
PYTHONPATH=. uvicorn backend.main:app --reload --port 8011
```

## API

- `POST /api/eval/run` (admin-only via `x-user-role: admin`)
- `GET /api/eval/latest`
- `GET /api/eval/history`
- `GET /api/eval/cases?run_id=...`

Each completed run regenerates `Docs/Architecture/Evals-Report.md`.

## Persistence

- If `SUPABASE_URL` + `SUPABASE_SERVICE_ROLE_KEY` are set, runs/cases persist to:
  - `evaluation_runs`
  - `evaluation_cases`
- Apply migration:
  - `phase-11-evaluation-suite/migrations/001_evaluation_tables.sql`
- Set `PHASE11_DISABLE_SUPABASE=true` to force local in-memory mode.
