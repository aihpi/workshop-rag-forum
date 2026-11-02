"""Fairness-aware reranking for the bias study.

DetGreedy lives here rather than in `workshop_rag_forum.retrieval` because it
reranks by a group label the study puts into `attrs`; the pipeline has no notion
of groups.
"""

from __future__ import annotations

import math

from typing_extensions import override

from workshop_rag_forum.embedding import Embedder
from workshop_rag_forum.retrieval import DenseRetriever
from workshop_rag_forum.store import VectorStore
from workshop_rag_forum.types import RetrievedChunk


class DetGreedyRetriever(DenseRetriever):
    """Fairness-aware reranking (DetGreedy, Geyik et al. 2019).

    Note the terminology trap: in RAG "reranker" normally means a *relevance*
    reranker, and `MMRRetriever` is a diversity one. This is neither. It
    enforces a **minimum representation** for each group in every prefix of the
    ranking, and is the only component here that targets representation directly.

    The algorithm walks the ranking position by position. Before filling
    position `i` (1-based) it computes each group's minimum required count,
    `floor(i * target[group])`. Any group already below its minimum is
    "starved"; the best-scoring remaining candidate from the starved groups wins
    the slot. If no group is starved, the best-scoring candidate overall wins.
    The prefix property matters: a top-10 that is fair only at rank 100 is not
    fair to anyone who reads the first page.

    `targets` are desired proportions per group. Passing the corpus base rates
    p0 asks for A = 1. Interpolating between the unreranked outcome and p0
    traces the trade-off curve against nDCG.

    Unlabelled candidates belong to no group, so they can never be starved. They
    are only ever placed when no group needs the slot, which keeps them from
    displacing the representation guarantee.
    """

    def __init__(
        self,
        store: VectorStore,
        embedder: Embedder,
        *,
        targets: dict[str, float],
        attr: str = "gender",
        pool: int = 300,
    ):
        super().__init__(store, embedder)
        if any(v < 0 for v in targets.values()):
            raise ValueError("targets must be non-negative")
        total = sum(targets.values())
        if total <= 0:
            raise ValueError("targets must not sum to zero")
        # Normalise so callers can pass raw counts or proportions.
        self.targets: dict[str, float] = {g: v / total for g, v in targets.items()}
        self.attr: str = attr
        self.pool: int = pool

    @property
    @override
    def name(self) -> str:
        shares = ",".join(f"{g}={p:.2f}" for g, p in sorted(self.targets.items()))
        return f"detgreedy({shares})"

    def _group_of(self, item: RetrievedChunk) -> str | None:
        value = item.chunk.attrs.get(self.attr)
        return str(value) if value is not None else None

    @override
    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        candidates = super().retrieve(query, k=max(self.pool, k))
        return rerank_detgreedy(candidates, self.targets, k=k, attr=self.attr)


def rerank_detgreedy(
    candidates: list[RetrievedChunk],
    targets: dict[str, float],
    *,
    k: int,
    attr: str = "gender",
) -> list[RetrievedChunk]:
    """Reorder `candidates` to meet `targets` in every prefix. Pure function.

    Kept separate from the retriever so the study can rerank a ranking it has
    already fetched, without paying for retrieval again per trade-off point.
    """
    remaining = list(candidates)
    by_group: dict[str | None, list[RetrievedChunk]] = {}
    for item in remaining:
        value = item.chunk.attrs.get(attr)
        by_group.setdefault(str(value) if value is not None else None, []).append(item)
    # Candidates arrive sorted by score; keep each group's queue in that order.

    selected: list[RetrievedChunk] = []
    counts: dict[str, int] = dict.fromkeys(targets, 0)

    for position in range(1, min(k, len(remaining)) + 1):
        starved = [
            group
            for group, share in targets.items()
            if by_group.get(group) and counts[group] < math.floor(position * share)
        ]
        if starved:
            # Best-scoring head among the groups that are behind quota.
            group = max(starved, key=lambda g: by_group[g][0].score)
            pick = by_group[group].pop(0)
            counts[group] += 1
        else:
            heads = [(g, q[0]) for g, q in by_group.items() if q]
            if not heads:
                break
            group, pick = max(heads, key=lambda pair: pair[1].score)
            by_group[group].pop(0)
            if group in counts:
                counts[group] += 1
        selected.append(pick)

    # Ranks describe the new order, not where the item came from.
    return [
        RetrievedChunk(chunk=item.chunk, score=item.score, rank=rank)
        for rank, item in enumerate(selected)
    ]
