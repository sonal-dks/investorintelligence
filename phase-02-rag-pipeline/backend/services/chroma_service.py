"""ChromaService — manages the persistent ChromaDB collection.

LLD reference: Phase 02 §Module Breakdown / ChromaService.

Refresh policy is **delete + create** (LLD: "for refresh: delete_collection() →
create_collection() → add()").  Cosine distance metric so we can convert to a
similarity score with ``1 - distance``.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, Sequence

import chromadb
from chromadb.api.models.Collection import Collection
from chromadb.config import Settings as ChromaClientSettings

from ..config.settings import SETTINGS
from ..models.schemas import Chunk

logger = logging.getLogger(__name__)


def _sanitize_metadata(meta: dict) -> dict:
    """Chroma metadata values must be scalar (no None / nested objects)."""
    clean: dict = {}
    for k, v in meta.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            clean[k] = v
        else:
            clean[k] = str(v)
    return clean


class ChromaService:
    def __init__(
        self,
        persist_dir: str | Path | None = None,
        collection_name: str | None = None,
    ) -> None:
        path = Path(persist_dir) if persist_dir else SETTINGS.chroma_path
        path.mkdir(parents=True, exist_ok=True)
        self.persist_dir = path
        self.collection_name = collection_name or SETTINGS.chroma_collection_name
        self._client = chromadb.PersistentClient(
            path=str(path),
            settings=ChromaClientSettings(anonymized_telemetry=False, allow_reset=True),
        )

    def get_or_create_collection(self) -> Collection:
        return self._client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def reset_collection(self) -> Collection:
        try:
            self._client.delete_collection(self.collection_name)
            logger.info(
                "chroma_collection_deleted",
                extra={"collection": self.collection_name},
            )
        except Exception as exc:  # noqa: BLE001 — fine if it never existed
            logger.info(
                "chroma_collection_delete_skipped",
                extra={"collection": self.collection_name, "reason": str(exc)},
            )
        return self._client.create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(
        self,
        chunks: Sequence[Chunk],
        embeddings: Iterable[list[float]],
        collection: Collection | None = None,
    ) -> int:
        col = collection or self.get_or_create_collection()
        ids = [c.id for c in chunks]
        documents = [c.text for c in chunks]
        metadatas = [_sanitize_metadata(c.metadata.model_dump()) for c in chunks]
        embeddings_list = [list(map(float, vec)) for vec in embeddings]
        if not (len(ids) == len(documents) == len(metadatas) == len(embeddings_list)):
            raise ValueError("chunks/embeddings length mismatch")
        if not ids:
            return 0
        col.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas,
            embeddings=embeddings_list,
        )
        return len(ids)

    def query(
        self,
        embedding: list[float],
        top_k: int,
        where: dict | None = None,
    ) -> list[dict]:
        col = self.get_or_create_collection()
        result = col.query(
            query_embeddings=[list(map(float, embedding))],
            n_results=max(1, top_k),
            where=where,
            include=["documents", "metadatas", "distances"],
        )
        ids = (result.get("ids") or [[]])[0]
        docs = (result.get("documents") or [[]])[0]
        metas = (result.get("metadatas") or [[]])[0]
        dists = (result.get("distances") or [[]])[0]
        out: list[dict] = []
        for cid, doc, meta, dist in zip(ids, docs, metas, dists, strict=False):
            score = max(0.0, 1.0 - float(dist))
            out.append({"id": cid, "text": doc, "metadata": meta, "score": score})
        return out

    def all_documents(self) -> list[dict]:
        """Return id + text + metadata for every doc (used to build BM25 index)."""

        col = self.get_or_create_collection()
        # Chroma .get() with no ids returns the full collection (paged at 10k by default)
        result = col.get(include=["documents", "metadatas"])
        ids = result.get("ids") or []
        docs = result.get("documents") or []
        metas = result.get("metadatas") or []
        out: list[dict] = []
        for cid, doc, meta in zip(ids, docs, metas, strict=False):
            out.append({"id": cid, "text": doc, "metadata": meta})
        return out

    def collection_size(self) -> int:
        return self.get_or_create_collection().count()
