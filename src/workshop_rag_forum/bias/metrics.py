"""Secondary diagnostics.

The headline metric lives in `ratio`. What is here answers a different question:
how few documents the pipeline draws on at all. It is not part of the outline,
but it is cheap to compute on the same run and explains some A values - an
occupation answered out of three articles cannot have a representative top-k.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Any

import numpy as np

from ..types import RetrievedChunk

# (query, retrieved passages)
RetrievalRun = tuple[str, list[RetrievedChunk]]


def rank_weight(rank: int) -> float:
    """DCG-style position weight: rank 0 counts most."""
    return 1.0 / math.log2(rank + 2)


def _shares(counts: dict[str, float]) -> dict[str, float]:
    total = sum(counts.values())
    return {k: (v / total if total else 0.0) for k, v in counts.items()}


def normalised_entropy(shares: Sequence[float]) -> float:
    """1.0 when perfectly even, 0.0 when one category takes everything."""
    positive = [s for s in shares if s > 0]
    if len(positive) <= 1:
        return 0.0
    entropy = -sum(s * math.log(s) for s in positive)
    return entropy / math.log(len(shares))


def gini(values: Sequence[float]) -> float:
    """Gini coefficient of a non-negative distribution. 0 = even, ->1 = concentrated."""
    array = np.sort(np.asarray(list(values), dtype=np.float64))
    if array.size == 0 or array.sum() <= 0:
        return 0.0
    n = array.size
    index = np.arange(1, n + 1)
    return float((2 * (index * array).sum()) / (n * array.sum()) - (n + 1) / n)


def herfindahl(shares: Sequence[float]) -> float:
    """Sum of squared shares. 1/HHI is the 'effective number' of categories."""
    return float(sum(s * s for s in shares))


def bootstrap_ci(
    samples: Sequence[float],
    *,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 0,
) -> tuple[float, float]:
    """Percentile bootstrap CI of the mean of `samples`."""
    values = np.asarray(list(samples), dtype=np.float64)
    if values.size == 0:
        return (float("nan"), float("nan"))
    if values.size == 1:
        return (float(values[0]), float(values[0]))
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, values.size, size=(n_resamples, values.size))
    stats = values[draws].mean(axis=1)
    alpha = (1 - confidence) / 2
    return float(np.quantile(stats, alpha)), float(np.quantile(stats, 1 - alpha))


def source_concentration(
    runs: Sequence[RetrievalRun],
    *,
    corpus_sources: Sequence[str] | None = None,
    rank_weighted: bool = True,
) -> dict[str, Any]:
    """How few sources supply the retrieved context."""
    counts: dict[str, float] = {}
    for _, retrieved in runs:
        for item in retrieved:
            weight = rank_weight(item.rank) if rank_weighted else 1.0
            counts[item.chunk.source] = counts.get(item.chunk.source, 0.0) + weight

    shares = sorted(_shares(counts).values(), reverse=True)
    hhi = herfindahl(shares)
    available = len(set(corpus_sources)) if corpus_sources is not None else None

    return {
        "n_queries": len(runs),
        "sources_retrieved": len(counts),
        "sources_available": available,
        "coverage": (len(counts) / available) if available else None,
        "top_source_share": shares[0] if shares else 0.0,
        "herfindahl": hhi,
        "effective_sources": (1 / hhi) if hhi else 0.0,
        "gini": gini(shares),
        "normalised_entropy": normalised_entropy(shares),
    }
