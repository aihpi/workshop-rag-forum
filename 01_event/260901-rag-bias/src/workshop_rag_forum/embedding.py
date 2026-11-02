"""Embedding backends.

`Embedder` is the seam the rest of the pipeline codes against, so the bias
harness can run end-to-end against `HashEmbedder` with no network at all, then
against the real endpoint by swapping one object.
"""

from __future__ import annotations

import hashlib
import time
from typing import Protocol, runtime_checkable

import numpy as np
from openai import OpenAI

from .config import Settings, get_settings


@runtime_checkable
class Embedder(Protocol):
    """Turns texts into unit-normalised float32 vectors."""

    @property
    def name(self) -> str: ...

    def embed(self, texts: list[str]) -> np.ndarray:
        """Return an (len(texts), dim) float32 array of unit vectors."""
        ...


def l2_normalise(vectors: np.ndarray) -> np.ndarray:
    """Unit-normalise rows so an inner product equals cosine similarity."""
    vectors = np.asarray(vectors, dtype=np.float32)
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return np.ascontiguousarray(vectors / np.maximum(norms, 1e-12), dtype=np.float32)


class OpenAIEmbedder:
    """Embeddings from any OpenAI-compatible endpoint, including a LiteLLM proxy."""

    def __init__(self, settings: Settings | None = None, client: OpenAI | None = None):
        self.settings: Settings = settings or get_settings()
        self._client: OpenAI = client or OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.api_base,
            timeout=self.settings.request_timeout,
        )

    @property
    def name(self) -> str:
        return self.settings.embedding_model

    def embed(self, texts: list[str]) -> np.ndarray:
        if not texts:
            return np.zeros((0, self.settings.embedding_dim or 0), dtype=np.float32)
        batches = [
            texts[i : i + self.settings.embed_batch]
            for i in range(0, len(texts), self.settings.embed_batch)
        ]
        return l2_normalise(np.vstack([self._embed_batch(b) for b in batches]))

    def _embed_batch(self, texts: list[str]) -> np.ndarray:
        """Embed one batch, shrinking inputs if the endpoint rejects their length.

        The endpoint's limit is in tokens while our chunker caps characters, so a
        dense batch can still overflow. Rather than abort a long ingest, shrink
        and retry; other errors are retried with backoff and then re-raised.
        """
        cap = self.settings.max_chars
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries):
            try:
                response = self._client.embeddings.create(
                    model=self.settings.embedding_model,
                    input=[t[:cap] for t in texts],
                )
                return np.array([d.embedding for d in response.data], dtype=np.float32)
            except Exception as error:  # noqa: BLE001 - classified below
                last_error = error
                if _is_too_long(error):
                    cap = max(32, int(cap * 0.8))
                elif _is_retryable(error):
                    time.sleep(2**attempt * 0.5)
                else:
                    raise
        raise RuntimeError(
            f"embedding failed after {self.settings.max_retries} attempts "
            f"(final char cap {cap})"
        ) from last_error


def _is_too_long(error: Exception) -> bool:
    text = str(error).lower()
    return "token" in text and any(
        w in text for w in ("less than", "maximum", "too long", "exceed")
    )


def _is_retryable(error: Exception) -> bool:
    status = getattr(error, "status_code", None)
    if status in (408, 409, 429) or (isinstance(status, int) and status >= 500):
        return True
    text = str(error).lower()
    return any(w in text for w in ("timeout", "connection", "rate limit"))


class HashEmbedder:
    """Deterministic offline embeddings: hashed word bag projected to `dim`.

    Not semantically meaningful, but stable and dependency-free, which is what
    tests and pipeline dry-runs need. Never use it for reported results.
    """

    def __init__(self, dim: int = 256):
        self.dim: int = dim

    @property
    def name(self) -> str:
        return f"hash-{self.dim}"

    def embed(self, texts: list[str]) -> np.ndarray:
        out = np.zeros((len(texts), self.dim), dtype=np.float32)
        for row, text in enumerate(texts):
            for word in text.lower().split():
                digest = hashlib.blake2b(word.encode(), digest_size=8).digest()
                bucket = int.from_bytes(digest[:4], "big") % self.dim
                sign = 1.0 if digest[4] % 2 else -1.0
                out[row, bucket] += sign
        return l2_normalise(out)
