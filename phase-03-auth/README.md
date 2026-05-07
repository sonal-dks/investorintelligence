# Phase 03 — Authentication + User Management

Implements Google OAuth via Supabase Auth, `user_profiles` with RLS, FastAPI profile API (JWT verified server-side), and a Vite/React client with role selection, first-login email capture, and admin route guarding.

## Prerequisites

- Supabase project with **Google** provider enabled and redirect URLs allowing `http://localhost:5173/**` (and your production origin).
- SQL migration applied: `migrations/003_user_profiles.sql`.

## Backend

```bash
cd phase-03-auth
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # fill SUPABASE_* values from Supabase dashboard
ruff check backend tests
pytest tests/ -v
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

JWT verification uses the **JWT secret** (Settings → API → JWT Settings), not the anon key.

## Frontend

```bash
cd frontend
cp .env.example .env        # VITE_SUPABASE_* + VITE_API_BASE
npm install
npm test
npm run dev
```

Open `/login`, pick a role, sign in with Google. After redirect, the app creates or loads the profile via `GET /api/users/me` and `POST /api/users/profile`.

## Success checks (Phase 03)

| Criterion | How to verify |
|-----------|----------------|
| OAuth + profile | Login; row appears in `user_profiles`. |
| Role persistence | Refresh; role matches selection. |
| First-login modal | Shown once until `first_login_complete` is true. |
| Sign out | Clears session and returns to `/login`. |
| Investor blocked from `/admin` | Open `/admin` as investor → redirect to `/dashboard`. |

## API

- `GET /api/users/me` — Bearer Supabase access token; `404` if no profile (client should `POST /profile`).
- `POST /api/users/profile` — partial updates; **`role` required** on first create.

## Layout

Deliverables live under this folder only: `backend/`, `frontend/`, `tests/`, `migrations/`, `expected_outputs/`.
