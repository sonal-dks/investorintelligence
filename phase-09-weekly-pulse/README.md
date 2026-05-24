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
python -m pytest tests -q --ignore=tests/e2e   # fast unit + API (in-memory)
```

### Live Supabase end-to-end (real `app_reviews`)
Requires `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, and **≥10** `app_reviews` rows dated in the current ISO week.

```bash
cd phase-09-weekly-pulse
python3 scripts/e2e_weekly_pulse_supabase.py
```

Or with pytest (subprocess-isolated):

```bash
RUN_PULSE_E2E=1 python3 -m pytest tests/e2e -m e2e -v
```

## LLM environment
- `OPENROUTER_API_KEY` — also auto-loaded from `phase-12-assembly-deploy/.env` or repo-root `longlist.env` if not set in this phase’s `.env`
- Optional: `PHASE09_LLM_PRIMARY_MODEL`, `PHASE09_LLM_FALLBACK_MODEL`
- Pulse uses OpenRouter for (1) batched **text** sentiment on the week’s reviews and (2) summary + specific themes (primary → fallback; JSON fenced responses tolerated)

## Supabase migration
- Apply: `migrations/001_weekly_pulse_llm_persistence.sql`
- Apply: `migrations/002_weekly_pulse_quotes_top_themes.sql` (`top_themes`, `user_quotes`)
- Required env for backend persistence:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_ROLE_KEY`
