# Phase 04 — Dashboard + App Shell

Phase 04 implements role-aware dashboard APIs and the app shell UI (sidebar, topbar, KPI strip, fund strip, booking summary, pulse preview).

## Backend

```bash
cd phase-04-dashboard
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -v
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Required env vars in `.env`:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET`
- `CORS_ORIGINS`

## Frontend

```bash
cd phase-04-dashboard/frontend
npm install
npm test
npm run build
npm run dev
```

Required env vars in `frontend/.env`:
- `VITE_SUPABASE_URL`
- `VITE_SUPABASE_ANON_KEY`
- `VITE_API_BASE`

## Success checks

- Investor and admin see role-scoped metrics.
- Dashboard KPIs use PRD Section 5.2 windows and trend logic.
- Empty states render for no activity/no fund data/no pulse data.
- App shell renders sidebar + topbar on authenticated routes.
