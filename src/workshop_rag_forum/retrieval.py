"""Retrievers: query text in, ranked chunks out.

Three variants, because the bias questions are mostly comparisons between them:

* `DenseRetriever`      - exact cosine, the reference behaviour.
* `MMRRetriever`        - diversity-aware reranking; a mitigation lever for
                          source concentration.
* `TurboVecRetriever`   - quantised search, reusing the 260615 meeting's index,
                          so "what does compression cost?" can be asked about
                          *who* gets retrieved rather than only recall@k.
"""

from __future__ import annotations

from typing import Any, Protocol, override, runtime_checkable

import numpy as np

from .embedding import Embedder, l2_normalise
from .store import VectorStore
from .types import RetrievedChunk


@runtime_checkable
class Retriever(Protocol):
    @property
    def name(self) -> str: ...

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]: ...


class DenseRetriever:
    """Exact cosine top-k over a `VectorStore`."""

    store: VectorStore
    embedder: Embedder

    def __init__(self, store: VectorStore, embedder: Embedder):
        self.store = store
        self.embedder = embedder

    @property
    def name(self) -> str:
        return "dense"

    def _embed_query(self, query: str) -> np.ndarray:
        return self.embedder.embed([query])[0]

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        scores, indices = self.store.search(self._embed_query(query), k=k)
        return [
            RetrievedChunk(chunk=self.store.chunks[idx], score=float(score), rank=rank)
            for rank, (score, idx) in enumerate(zip(scores[0], indices[0], strict=True))
        ]


class MMRRetriever(DenseRetriever):
    """Maximal Marginal Relevance reranking of a wider candidate pool.

    Picks each next chunk to maximise `lambda * relevance - (1 - lambda) * max
    similarity to what is already selected`, so near-duplicate passages from one
    dominant source stop crowding out the rest of the top-k.
    """

    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        *,
        lambda_: float = 0.5,
        pool: int = 30,
    ):
        super().__init__(store, embedder)
        if not 0.0 <= lambda_ <= 1.0:
            raise ValueError("lambda_ must be in [0, 1]")
        self.lambda_: float = lambda_
        self.pool: int = pool

    @property
    @override
    def name(self) -> str:
        return f"mmr(lambda={self.lambda_})"

    @override
    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        query_vector = self._embed_query(query)
        scores, indices = self.store.search(query_vector, k=max(self.pool, k))
        # Work in pool-local positions throughout; map back to store rows at the end.
        pool_rows = [int(i) for i in indices[0]]
        relevance = np.asarray(scores[0], dtype=np.float32)
        vectors = self.store.vectors[pool_rows]
        similarity = vectors @ vectors.T  # pool x pool, computed once

        remaining = list(range(len(pool_rows)))
        selected: list[int] = []
        # Running max similarity of each candidate to the selected set.
        penalty = np.zeros(len(pool_rows), dtype=np.float32)
        while remaining and len(selected) < k:
            values = (
                self.lambda_ * relevance[remaining]
                - (1 - self.lambda_) * penalty[remaining]
            )
            best = remaining[int(np.argmax(values))] if selected else remaining[0]
            selected.append(best)
            remaining.remove(best)
            penalty = np.maximum(penalty, similarity[best])

        return [
            RetrievedChunk(
                chunk=self.store.chunks[pool_rows[pos]],
                score=float(relevance[pos]),
                rank=rank,
            )
            for rank, pos in enumerate(selected)
        ]


class TurboVecRetriever(DenseRetriever):
    """Retrieval over a turbovec-quantised copy of the store's vectors."""

    def __init__(self, store: VectorStore, embedder: Embedder, *, bit_width: int = 4):
        super().__init__(store, embedder)
        try:
            from turbovec import TurboQuantIndex  # type: ignore[import-untyped]
        except ImportError as error:  # pragma: no cover - optional dependency
            raise ImportError(
                "TurboVecRetriever needs the `turbovec` package (uv add turbovec)"
            ) from error
        self.bit_width: int = bit_width
        self._index: Any = TurboQuantIndex(dim=store.dim, bit_width=bit_width)
        self._index.add(l2_normalise(store.vectors))
        self._index.prepare()

    @property
    @override
    def name(self) -> str:
        return f"turbovec-{self.bit_width}bit"

    @override
    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        query_vector = l2_normalise(self._embed_query(query).reshape(1, -1))
        scores, ids = self._index.search(query_vector, k=k)
        return [
            RetrievedChunk(
                chunk=self.store.chunks[int(idx)], score=float(score), rank=rank
            )
            for rank, (score, idx) in enumerate(
                zip(np.asarray(scores)[0], np.asarray(ids)[0], strict=True)
            )
        ]
