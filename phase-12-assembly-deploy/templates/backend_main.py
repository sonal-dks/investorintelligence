"""Phase-12 assembled backend entrypoint.

This app mounts each phase backend under a dedicated URL prefix and exposes
a single health endpoint for Render checks.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _load_asgi_app(module_file: Path, attr_name: str):
    module_name = f"assembled_{module_file.parent.parent.parent.name}_{module_file.stem}"
    phase_root = module_file.parent.parent
    sys.path.insert(0, str(phase_root))
    spec = importlib.util.spec_from_file_location(module_name, module_file)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load module: {module_file}")
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)  # type: ignore[union-attr]
        return getattr(module, attr_name)
    finally:
        if sys.path and sys.path[0] == str(phase_root):
            sys.path.pop(0)


ROOT = Path(__file__).resolve().parents[1]
PHASES = ROOT / "phases"

app = FastAPI(title="InvestorIntelligence Assembled Backend", version="1.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "phase": "12-assembly-deploy"}


MOUNT_TARGETS: list[tuple[str, Path, str]] = [
    ("/api/rag", PHASES / "phase-02-rag-pipeline" / "backend" / "app.py", "app"),
    ("/api/auth", PHASES / "phase-03-auth" / "backend" / "main.py", "app"),
    ("/api/dashboard", PHASES / "phase-04-dashboard" / "backend" / "main.py", "app"),
    ("/api/chat", PHASES / "phase-05-smart-search" / "backend" / "main.py", "app"),
    ("/api/voice", PHASES / "phase-06-voice-agent" / "backend" / "main.py", "app"),
    ("/api/approvals", PHASES / "phase-07-intent-approvals" / "backend" / "main.py", "app"),
    ("/api/bookings", PHASES / "phase-08-calendar-booking" / "backend" / "main.py", "app"),
    ("/api/pulse", PHASES / "phase-09-weekly-pulse" / "backend" / "main.py", "app"),
    ("/api/resources", PHASES / "phase-10-explorer-resources" / "backend" / "main.py", "app"),
    ("/api/evals", PHASES / "phase-11-evaluation-suite" / "backend" / "main.py", "app"),
]

loaded = []
for prefix, module_file, attr_name in MOUNT_TARGETS:
    if not module_file.exists():
        continue
    try:
        app.mount(prefix, _load_asgi_app(module_file, attr_name))
        loaded.append(prefix)
    except Exception as exc:  # pragma: no cover - startup telemetry only
        # Keep startup resilient; failed mount is surfaced in health payload.
        loaded.append(f"{prefix} (failed: {exc})")


@app.get("/health/details")
def health_details() -> dict[str, object]:
    return {"status": "ok", "mounted_services": loaded}
