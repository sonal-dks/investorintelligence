# Phase 07 - Intent Detection + Approval Center

## Run backend

```bash
cd phase-07-intent-approvals
python3 -m venv .venv && source .venv/bin/activate
pip install -r backend/requirements.txt
PYTHONPATH=. uvicorn backend.main:app --reload --port 8003
```

## Run tests

```bash
cd phase-07-intent-approvals
PYTHONPATH=. pytest -q
```

## Frontend deliverables
- `frontend/src/pages/ApprovalCenter.tsx`
- `frontend/src/components/ApprovalList.tsx`
- `frontend/src/components/ApprovalDetail.tsx`
- `frontend/src/components/EmailPreview.tsx`
- `frontend/src/stores/approval-store.ts`
