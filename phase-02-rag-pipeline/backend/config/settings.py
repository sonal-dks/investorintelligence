"""Centralized settings for the Phase 02 RAG pipeline.

All values are read from environment (with sensible defaults).  The .env file
in `phase-02-rag-pipeline/` is loaded automatically when this module is imported.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

_HERE = Path(__file__).resolve().parents[2]
load_dotenv(_HERE / ".env")


@dataclass(frozen=True)
class RAGSettings:
    supabase_url: str
    supabase_service_role_key: str
    chroma_persist_dir: str
    embedding_model: str
    embedding_fallback_model: str
    chroma_collection_name: str
    default_top_k: int
    dynamic_k_min: int
    dynamic_k_max: int
    score_threshold: float
    entity_fuzz_threshold: int

    @property
    def chroma_path(self) -> Path:
        p = Path(self.chroma_persist_dir)
        if not p.is_absolute():
            p = _HERE / p
        return p


def load_settings() -> RAGSettings:
    return RAGSettings(
        supabase_url=os.getenv("SUPABASE_URL", ""),
        supabase_service_role_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
        chroma_persist_dir=os.getenv("CHROMA_PERSIST_DIR", "./chroma_data"),
        embedding_model=os.getenv("EMBEDDING_MODEL", "BAAI/bge-large-en-v1.5"),
        embedding_fallback_model=os.getenv(
            "EMBEDDING_FALLBACK_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
        ),
        chroma_collection_name=os.getenv("CHROMA_COLLECTION_NAME", "mutual_fund_knowledge"),
        default_top_k=int(os.getenv("RAG_DEFAULT_TOP_K", "5")),
        dynamic_k_min=int(os.getenv("RAG_DYNAMIC_K_MIN", "3")),
        dynamic_k_max=int(os.getenv("RAG_DYNAMIC_K_MAX", "12")),
        score_threshold=float(os.getenv("RAG_SCORE_THRESHOLD", "0.3")),
        entity_fuzz_threshold=int(os.getenv("RAG_ENTITY_FUZZ_THRESHOLD", "70")),
    )


SETTINGS = load_settings()
