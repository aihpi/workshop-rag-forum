"""The study's headline metric: A = p_k / p0.

For a query, p0 is the base rate of a group in the **relevant set** - the corpus
people who actually have the occupation being asked about - and p_k is that
group's share of the top-k. Their ratio says how the retriever moved the group
relative to what was available:

    A = 1    neutral: the top-k mirrors the pool
    A > 1    amplified
    A < 1    suppressed

A ratio rather than a difference of shares, because a ratio is scale-free in p0.
A 10-point share gap means something very different against a 50% base rate than
against a 5% one; A does not have that problem, which is what makes variants R
and K comparable to each other at all.

Two deliberate refusals to report:

* **Below `MIN_N_FOR_CI` people in the pool, no confidence interval** - only the
  raw n. Resampling 4 people produces an interval, but not an honest one.
* **p0 = 0 yields A = None**, never infinity. A group absent from the pool cannot
  be amplified by retrieval.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from ..types import RetrievedChunk

# Below this many people in the relevant set, report n instead of an interval.
MIN_N_FOR_CI = 30


def _share(items: Sequence[str], group: str) -> float:
    return sum(1 for i in items if i == group) / len(items) if items else 0.0


def amplification(
    retrieved_groups: Sequence[str],
    pool_groups: Sequence[str],
    group: str,
) -> float | None:
    """A = p_k/p0 for one group. None when the group is absent from the pool."""
    p0 = _share(pool_groups, group)
    if p0 <= 0:
        return None
    return _share(retrieved_groups, group) / p0


def bootstrap_amplification(
    retrieved_groups: Sequence[str],
    pool_groups: Sequence[str],
    group: str,
    *,
    n_resamples: int = 2000,
    confidence: float = 0.95,
    seed: int = 0,
) -> tuple[float, float] | None:
    """Percentile bootstrap CI for A, resampling the retrieved slots.

    p0 is held fixed: it is a full census of the corpus pool, not a sample, so
    the uncertainty being quantified is in *what got retrieved*. Slots within one
    query are not independent, which makes this interval mildly optimistic -
    stated in the meeting README rather than hidden.
    """
    # The threshold is on *this group's* count, not the pool total: the case it
    # exists for is a group with a handful of people in an otherwise large pool.
    n_group = sum(1 for g in pool_groups if g == group)
    p0 = _share(pool_groups, group)
    if p0 <= 0 or not retrieved_groups or n_group < MIN_N_FOR_CI:
        return None
    hits = np.array([1.0 if g == group else 0.0 for g in retrieved_groups])
    rng = np.random.default_rng(seed)
    draws = rng.integers(0, hits.size, size=(n_resamples, hits.size))
    stats = hits[draws].mean(axis=1) / p0
    alpha = (1 - confidence) / 2
    return float(np.quantile(stats, alpha)), float(np.quantile(stats, 1 - alpha))


def in_relevant_set(chunk_attrs: dict[str, Any], occupation: str | None) -> bool:
    """Is this hit a member of the occupation the query asked about?

    P106 is multi-valued, so membership is a set test, not equality.
    """
    if occupation is None:
        return True
    occupations = chunk_attrs.get("occupations")
    if isinstance(occupations, list):
        return occupation in occupations
    return chunk_attrs.get("occupation") == occupation


def stratum_amplification(
    runs: Sequence[tuple[str, list[RetrievedChunk]]],
    pool_groups: Sequence[str],
    groups: Sequence[str],
    *,
    k: int,
    occupation: str | None = None,
    attr: str = "gender",
    seed: int = 0,
) -> dict[str, Any]:
    """A per group for one occupation stratum, pooled over its query phrasings.

    p_k counts only hits that are actually in the relevant set - people who hold
    the occupation being asked about. Retrieval runs over the whole corpus, so a
    query for actors also returns footballers; counting those in p_k while p0 is
    computed over actors alone would compare two different populations. Off-topic
    hits are reported as `off_topic_share`, which doubles as a retrieval-quality
    signal, and unlabelled hits as `unlabelled_share`.
    """
    retrieved_groups: list[str] = []
    unlabelled = off_topic = total_slots = 0
    per_query: dict[str, dict[str, float | None]] = {}

    for query, retrieved in runs:
        top = retrieved[:k]
        total_slots += len(top)
        labels: list[str] = []
        for chunk in top:
            attrs = chunk.chunk.attrs
            if attrs.get(attr) is None:
                unlabelled += 1
                continue
            if not in_relevant_set(attrs, occupation):
                off_topic += 1
                continue
            labels.append(str(attrs[attr]))
        retrieved_groups.extend(labels)
        per_query[query] = {g: amplification(labels, pool_groups, g) for g in groups}

    pool_counts = {g: sum(1 for p in pool_groups if p == g) for g in groups}
    result: dict[str, Any] = {
        "k": k,
        "n_queries": len(runs),
        "n_pool": len(pool_groups),
        "pool_counts": pool_counts,
        "base_rate": {g: _share(pool_groups, g) for g in groups},
        "top_k_share": {g: _share(retrieved_groups, g) for g in groups},
        "amplification": {
            g: amplification(retrieved_groups, pool_groups, g) for g in groups
        },
        "amplification_ci95": {},
        "ci_suppressed": {},
        "per_query_amplification": per_query,
        "n_in_relevant_set": len(retrieved_groups),
        "unlabelled_share": unlabelled / max(1, total_slots),
        "off_topic_share": off_topic / max(1, total_slots),
    }

    for group in groups:
        interval = bootstrap_amplification(
            retrieved_groups, pool_groups, group, seed=seed
        )
        result["amplification_ci95"][group] = list(interval) if interval else None
        # Say *why* an interval is missing, so a blank cell is never ambiguous.
        if interval is None:
            result["ci_suppressed"][group] = (
                "absent from pool"
                if pool_counts[group] == 0
                else f"n={pool_counts[group]} < {MIN_N_FOR_CI}"
            )
    return result
