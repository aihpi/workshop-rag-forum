"""Persistent chunk store: text, metadata and vectors kept together.

The turbovec meeting saved vectors only, so a retrieved row index pointed at
nothing. Here every vector row `i` corresponds to `chunks[i]`, and both are
written side by side, which is what makes generation (and provenance-based bias
metrics) possible at all.

On disk:
    <dir>/chunks.parquet   text + provenance + attributes, row-aligned to vectors
    <dir>/vectors.npy      (n, dim) float32, unit-normalised
    <dir>/meta.json        embedder name, dim, count
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .embedding import Embedder, l2_normalise
from .types import Chunk


class VectorStore:
    """An in-memory store with exact cosine search and on-disk persistence."""

    def __init__(
        self,
        chunks: list[Chunk] | None = None,
        vectors: np.ndarray | None = None,
        embedder_name: str = "",
    ):
        self.chunks: list[Chunk] = list(chunks or [])
        dim = int(vectors.shape[1]) if vectors is not None and vectors.size else 0
        self.vectors: np.ndarray = (
            np.asarray(vectors, dtype=np.float32)
            if vectors is not None
            else np.zeros((0, dim), dtype=np.float32)
        )
        self.embedder_name: str = embedder_name
        self._validate()

    def _validate(self) -> None:
        if len(self.chunks) != len(self.vectors):
            raise ValueError(
                f"{len(self.chunks)} chunks but {len(self.vectors)} vectors; "
                "text and vectors must stay row-aligned"
            )

    def __len__(self) -> int:
        return len(self.chunks)

    @property
    def dim(self) -> int:
        return int(self.vectors.shape[1]) if self.vectors.size else 0

    # ---- building -------------------------------------------------------

    @classmethod
    def build(cls, chunks: list[Chunk], embedder: Embedder) -> VectorStore:
        """Embed `chunks` and return a store holding both."""
        vectors = embedder.embed([c.text for c in chunks])
        return cls(chunks=chunks, vectors=vectors, embedder_name=embedder.name)

    def add(self, chunks: list[Chunk], embedder: Embedder) -> None:
        if not chunks:
            return
        vectors = embedder.embed([c.text for c in chunks])
        self.chunks.extend(chunks)
        self.vectors = (
            vectors if not self.vectors.size else np.vstack([self.vectors, vectors])
        )
        self.embedder_name = self.embedder_name or embedder.name
        self._validate()

    # ---- search ---------------------------------------------------------

    def search(
        self, query_vectors: np.ndarray, k: int = 5
    ) -> tuple[np.ndarray, np.ndarray]:
        """Exact cosine top-k. Returns (scores, indices), both (n_queries, k)."""
        if not len(self):
            raise ValueError("store is empty")
        queries = l2_normalise(np.atleast_2d(query_vectors))
        if queries.shape[1] != self.dim:
            raise ValueError(
                f"query dim {queries.shape[1]} != store dim {self.dim}; "
                "the store was probably built with a different embedding model"
            )
        k = min(k, len(self))
        sims = queries @ self.vectors.T
        # argpartition then sort only the k survivors: O(n) instead of O(n log n).
        top = np.argpartition(-sims, kth=k - 1, axis=1)[:, :k]
        ordered = np.take_along_axis(
            top, np.argsort(-np.take_along_axis(sims, top, axis=1), axis=1), axis=1
        )
        return np.take_along_axis(sims, ordered, axis=1), ordered

    # ---- persistence ----------------------------------------------------

    def save(self, directory: Path) -> None:
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        rows: list[dict[str, Any]] = []
        for chunk in self.chunks:
            row = chunk.to_row()
            # attrs holds mixed types; a JSON string round-trips losslessly.
            row["attrs"] = json.dumps(row["attrs"], sort_keys=True)
            rows.append(row)
        pd.DataFrame(rows).to_parquet(directory / "chunks.parquet", index=False)
        np.save(directory / "vectors.npy", self.vectors)
        (directory / "meta.json").write_text(
            json.dumps(
                {
                    "embedder": self.embedder_name,
                    "dim": self.dim,
                    "n_chunks": len(self),
                },
                indent=2,
            )
        )

    @classmethod
    def load(cls, directory: Path) -> VectorStore:
        directory = Path(directory)
        chunks_path = directory / "chunks.parquet"
        if not chunks_path.exists():
            raise FileNotFoundError(
                f"no store at {directory}; run `workshop-rag ingest` first"
            )
        frame = pd.read_parquet(chunks_path)
        chunks = [
            Chunk(
                chunk_id=str(row["chunk_id"]),
                doc_id=str(row["doc_id"]),
                text=str(row["text"]),
                source=str(row["source"]),
                title=str(row["title"]),
                ordinal=int(row["ordinal"]),
                attrs=json.loads(row["attrs"]) if row["attrs"] else {},
            )
            for row in frame.to_dict("records")
        ]
        vectors = np.load(directory / "vectors.npy")
        meta_path = directory / "meta.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {}
        return cls(chunks, vectors, embedder_name=meta.get("embedder", ""))
