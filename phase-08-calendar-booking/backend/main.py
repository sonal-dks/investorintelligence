"""Phase 08 FastAPI application."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routers.booking_router import router as booking_router
from backend.routers.calendar_router import router as calendar_router

app = FastAPI(title="Phase 08 Calendar + Booking API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(booking_router)
app.include_router(calendar_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "08-calendar-booking"}
