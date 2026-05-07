from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.pulse_router import router as pulse_router

app = FastAPI(title="Phase 09 Weekly Pulse API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(pulse_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "09-weekly-pulse"}
