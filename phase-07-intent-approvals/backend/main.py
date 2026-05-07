"""Phase 07 FastAPI app — Intent Detection + Approval Center API."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.approval_router import router as approval_router

app = FastAPI(title="Phase 07 Intent + Approvals API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(approval_router)


@app.get('/health')
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "07-intent-approvals"}
