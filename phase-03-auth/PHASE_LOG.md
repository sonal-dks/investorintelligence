# Phase 03 — Implementation log

## Goal

Google OAuth (Supabase Auth), `user_profiles` + RLS, profile REST API, React login shell with role selection, first-login email capture, session persistence, sign-out, investor/admin route guard.

## Changes

- Added `phase-03-auth/` tree: FastAPI backend, Vite/React frontend, SQL migration, pytest + vitest, `expected_outputs/user_profile.json`.

## Checks run

| Check | Result |
|-------|--------|
| `ruff check backend tests` | PASS |
| `pytest tests/ -v` | PASS |
| `npm test` (frontend) | PASS |
| `npm run build` (tsc + vite) | PASS |
| eslint | Not configured in this phase (LLD optional; add with Phase 04 shell if desired) |
| mypy | Not required for Phase 03 scope |
| Manual OAuth → Supabase | Requires user project + Google provider (documented in README) |

## Debug notes

- Backend uses **service role** for `user_profiles` writes; **JWT `sub`** is the only user identity (never accept `user_id` from body).
- `GET /api/users/me` returns **404** without a row; client creates via `POST /api/users/profile` with pending role from `localStorage`.
- RLS policies target `authenticated` for direct PostgREST access; API path bypasses RLS with service role.

## Result

**PASS** (automated gates). **Runtime OAuth** depends on Supabase + Google configuration.

## Next step

Phase 04 — Dashboard + app shell.
