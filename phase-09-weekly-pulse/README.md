# Phase 09 - Weekly Pulse

Implements weekly review intelligence:
- Sentiment classification from star ratings
- Theme and keyword trend extraction
- Weekly pulse summary with exactly 3 action items
- Judge validation before publication
- Frontend tabs: Overview, Reviews, Keywords
- Generation chain: primary LLM -> fallback LLM -> deterministic fallback
- Dashboard comparison: LLM output vs deterministic output (side-by-side)
- Downstream `themes` field is LLM-only for email/voice integrations

## Backend endpoints
- `POST /api/pulse/generate` (admin-only via `x-user-role: admin`)
- `GET /api/pulse/latest`
- `GET /api/pulse/reviews?sentiment=&page=&limit=`
- `GET /api/pulse/keywords`
- `GET /api/pulse/trends`

## Run tests
```bash
cd phase-09-weekly-pulse
python -m pytest tests -q
```

## LLM environment
- `OPENROUTER_API_KEY`
- Optional: `PHASE09_LLM_PRIMARY_MODEL`, `PHASE09_LLM_FALLBACK_MODEL`

## Supabase migration
- Apply: `phase-09-weekly-pulse/migrations/001_weekly_pulse_llm_persistence.sql`
- Required env for backend persistence:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
