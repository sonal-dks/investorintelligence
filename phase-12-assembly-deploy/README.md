# Phase 12 - Assembly + Deployment Runbook

This folder implements deployment assembly for:
- **Frontend** -> Vercel (`frontend-deploy/`)
- **Backend** -> Render (`backend-deploy/`)

## Deliverables in this folder

- `scripts/assemble-backend.sh`
- `scripts/assemble-frontend.sh`
- `ci/deploy.yml`
- `smoke-tests/smoke_test.py`
- `env.example`

## 1) Assemble deploy directories

From repo root:

```bash
chmod +x phase-12-assembly-deploy/scripts/*.sh
phase-12-assembly-deploy/scripts/assemble-backend.sh
phase-12-assembly-deploy/scripts/assemble-frontend.sh
```

### Unified local development

From the **repository root**, after `npm install` at the repo root and `npm ci --prefix phase-07-intent-approvals/frontend` (needed for TypeScript when building the embedded Approval Center):

```bash
npm run dev:all
```

This runs `assemble-backend.sh`, then **concurrently** starts the assembled FastAPI app on **127.0.0.1:8012** and the Phase 04 Vite dev server (port **5180**), with the dashboard proxying `/api` traffic to the assembled API. Use an empty `VITE_API_BASE` in the dashboard `.env` for same-origin requests through the proxy.

Outputs:
- `backend-deploy/`
- `frontend-deploy/`

## 2) Backend deploy (Render)

1. Create a new Render Web Service.
2. Connect this repository.
3. Set **Root Directory** to `backend-deploy`.
4. Build command:
   - `pip install -r requirements.txt`
5. Start command:
   - `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
6. Health check path:
   - `/health`
7. Attach persistent disk:
   - Mount path: `/var/data/chroma`
   - Set env: `CHROMA_PERSIST_DIR=/var/data/chroma`
8. Add backend env vars from `phase-12-assembly-deploy/env.example`.

## 3) Frontend deploy (Vercel)

1. Import this GitHub repository in Vercel.
2. Set **Root Directory** to `frontend-deploy`.
3. Framework preset: Vite.
4. Build command: `npm run build`
5. Output directory: `dist`
6. Add frontend env vars from `phase-12-assembly-deploy/env.example`.

## 4) CI/CD

Workflow file:
- `.github/workflows/deploy-phase12.yml`

This runs on push to `main` and manual dispatch:
- assembles backend/frontend deploy folders,
- validates assembled backend entrypoint syntax,
- builds assembled frontend,
- uploads deploy artifacts.

## 5) Smoke tests (post deploy)

```bash
BACKEND_BASE_URL=https://your-render-url.onrender.com \
python phase-12-assembly-deploy/smoke-tests/smoke_test.py
```

Expected:
- `/health` -> `200`
- `/health/details` -> `200`

## Notes

- Keep secrets only in Render/Vercel/GitHub env settings (never commit real values).
- If frontend cannot call backend in production, validate `ALLOWED_ORIGINS` first.
