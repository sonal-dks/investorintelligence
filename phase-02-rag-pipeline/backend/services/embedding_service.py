"""EmbeddingService — wraps sentence-transformers with primary/fallback policy.

Primary: BAAI/bge-large-en-v1.5 (1024-dim, ~2GB RAM).
Fallback: sentence-transformers/all-MiniLM-L6-v2 (384-dim, ~100MB).

Per AI-ML Fallback skill: keep the output contract identical (numpy float32
array of shape ``(n, dim)``) and surface which model executed via ``model_name``.

The service is **lazy**: weights load only on first ``encode_*`` call so that
unit tests for chunking / entity-resolution don't need the 2GB download.
"""

from __future__ import annotations

import logging
import time
from threading import Lock
from typing import Iterable

import numpy as np

from ..config.settings import SETTINGS

logger = logging.getLogger(__name__)

BGE_QUERY_INSTRUCTION = "Represent this sentence for searching relevant passages: "


class EmbeddingService:
    def __init__(
        self,
        primary_model: str | None = None,
        fallback_model: str | None = None,
    ) -> None:
        self.primary_name = primary_model or SETTINGS.embedding_model
        self.fallback_name = fallback_model or SETTINGS.embedding_fallback_model
        self._model = None
        self._model_name: str | None = None
        self._dim: int | None = None
        self._lock = Lock()

    def _load(self) -> None:
        with self._lock:
            if self._model is not None:
                return
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415

            for candidate in (self.primary_name, self.fallback_name):
                try:
                    logger.info("embedding_model_load_attempt", extra={"model": candidate})
                    started = time.time()
                    model = SentenceTransformer(candidate)
                    self._model = model
                    self._model_name = candidate
                    self._dim = int(model.get_sentence_embedding_dimension())
                    logger.info(
                        "embedding_model_loaded",
                        extra={
                            "model": candidate,
                            "dim": self._dim,
                            "load_time_ms": int((time.time() - started) * 1000),
                        },
                    )
                    return
                except Exception as exc:  # noqa: BLE001 - we want to fall back on any load error
                    logger.warning(
                        "embedding_model_load_failed",
                        extra={"model": candidate, "error": str(exc)},
                    )
            raise RuntimeError(
                f"Failed to load embedding model (primary={self.primary_name}, "
                f"fallback={self.fallback_name})"
            )

    @property
    def model_name(self) -> str:
        if self._model_name is None:
            self._load()
        assert self._model_name is not None
        return self._model_name

    @property
    def dim(self) -> int:
        if self._dim is None:
            self._load()
        assert self._dim is not None
        return self._dim

    def encode_passages(self, texts: Iterable[str], batch_size: int = 64) -> np.ndarray:
        text_list = list(texts)
        if not text_list:
            return np.zeros((0, self.dim), dtype=np.float32)
        self._load()
        assert self._model is not None
        vectors = self._model.encode(
            text_list,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vectors.astype(np.float32, copy=False)

    def encode_query(self, text: str) -> np.ndarray:
        self._load()
        assert self._model is not None
        prefixed = (
            BGE_QUERY_INSTRUCTION + text if "bge" in self.model_name.lower() else text
        )
        vector = self._model.encode(
            [prefixed],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return vector.astype(np.float32, copy=False)[0]

    def validate_dim(self, vector: np.ndarray) -> None:
        if vector.ndim == 1:
            actual = vector.shape[0]
        else:
            actual = vector.shape[-1]
        if actual != self.dim:
            raise ValueError(
                f"embedding dimension mismatch: expected {self.dim}, got {actual}"
            )
