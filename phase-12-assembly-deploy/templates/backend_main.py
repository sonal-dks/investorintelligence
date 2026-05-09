"""Phase-12 assembled backend: one process, isolated phase packages, merged routers."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parents[1]
PACKAGES = ROOT / "packages"
sys.path.insert(0, str(PACKAGES))


def _include_router(app: FastAPI, label: str, import_path: str, attr: str) -> str:
    try:
        mod = importlib.import_module(import_path)
        router = getattr(mod, attr)
        app.include_router(router)
        return label
    except Exception as exc:  # pragma: no cover - startup telemetry
        return f"{label} (failed: {exc!r})"


_cors = os.getenv("ASSEMBLED_CORS_ORIGINS", "*").strip()
_origins = ["*"] if _cors == "*" else [o.strip() for o in _cors.split(",") if o.strip()]

app = FastAPI(title="InvestorIntelligence Assembled Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "12-assembly-deploy"}


# Each tuple: (label, module_path, router_attribute)
_ROUTER_SPECS: list[tuple[str, str, str]] = [
    ("rag", "backend_ph02.routers.rag_router", "router"),
    ("users", "backend_ph03.routers.user_router", "router"),
    ("dashboard", "backend_ph04.routers.dashboard_router", "router"),
    ("chat", "backend_ph05.routers.chat_router", "router"),
    ("voice", "backend_ph06.routers.voice_router", "router"),
    ("approvals", "backend_ph07.routers.approval_router", "router"),
    ("bookings", "backend_ph08.routers.booking_router", "router"),
    ("calendar", "backend_ph08.routers.calendar_router", "router"),
    ("pulse", "backend_ph09.routers.pulse_router", "router"),
    ("funds", "backend_ph10.routers.fund_router", "router"),
    ("eval", "backend_ph11.routers.eval_router", "router"),
]

_mounted: list[str] = []
for label, modpath, attr in _ROUTER_SPECS:
    _mounted.append(_include_router(app, label, modpath, attr))


@app.get("/health/details")
def health_details() -> dict[str, object]:
    return {"status": "ok", "mounted_services": _mounted}
