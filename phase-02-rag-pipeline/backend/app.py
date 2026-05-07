"""FastAPI app for local Phase 02 development.

Run with:
    uvicorn phase-02-rag-pipeline.backend.app:app --reload --port 8002
"""

from __future__ import annotations

import logging

from fastapi import FastAPI

from .routers import rag_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s :: %(message)s",
)


def create_app() -> FastAPI:
    app = FastAPI(title="Investor Ops Suite — Phase 02 RAG", version="0.1.0")
    app.include_router(rag_router.router)

    @app.get("/health")
    def root_health() -> dict:
        return {"status": "ok", "phase": 2}

    return app


app = create_app()
