"""Retrieval quality, so a fairness intervention can be priced.

Reranking for representation always costs relevance. Reporting the gain in A
without the loss in ranking quality would make every intervention look free, so
the study needs a quality number measured on the same run.

Relevance here is **binary and objective**: a hit is relevant if the person holds
the occupation the query asked about, which Wikidata already tells us. No human
judgements, no LLM judge. It is a coarse definition (it cannot say that one actor
is a better answer than another), so treat nDCG here as "how much on-topic
material stayed near the top", not as a general IR score.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

from ..types import RetrievedChunk
from .ratio import in_relevant_set


def relevance(hit: RetrievedChunk, occupation: str | None) -> float:
    """1.0 if the hit is in the relevant set, else 0.0."""
    return 1.0 if in_relevant_set(hit.chunk.attrs, occupation) else 0.0


def dcg(gains: Sequence[float]) -> float:
    """Discounted cumulative gain, log2 discount, 1-based positions."""
    return sum(g / math.log2(i + 2) for i, g in enumerate(gains))


def ndcg_at_k(
    retrieved: Sequence[RetrievedChunk],
    occupation: str | None,
    *,
    k: int,
) -> float:
    """nDCG@k against binary occupation relevance.

    The ideal ranking is every relevant hit first, drawn from the same retrieved
    set. This measures how well the *ordering* uses what retrieval found, which
    is the right question when comparing a reranker against its own input: the
    candidate pool is identical, only the order differs.
    """
    gains = [relevance(hit, occupation) for hit in retrieved[:k]]
    if not gains:
        return 0.0
    ideal = dcg(sorted(gains, reverse=True))
    return (dcg(gains) / ideal) if ideal > 0 else 0.0
