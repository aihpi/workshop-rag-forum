"""Article length as a covariate (outline section 10).

A plausible innocent explanation for a low A: the retriever prefers longer
articles, and one group's articles happen to be shorter. That is still a real
effect on who gets found, but it is a *different* mechanism from the embedding
associating a query with a gender, and the two call for different fixes.

The control used here is stratification rather than regression. The relevant set
is cut into length terciles, and A is recomputed inside each one. Within a
tercile the groups have near-identical article lengths, so length can no longer
explain a gap:

* A moves to ~1 inside every tercile  ->  length accounted for the whole effect.
* A stays away from 1 inside terciles ->  something other than length is at work.

Stratification is used deliberately in preference to fitting a model. It assumes
nothing about functional form, the output is readable without statistics, and it
degrades honestly: a tercile with too few people of a group simply reports its n
and no interval, exactly as the main metric does.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np

from ..types import RetrievedChunk
from .ratio import in_relevant_set, stratum_amplification

TERCILE_NAMES = ["short", "medium", "long"]


def length_profile(
    store_chunks: Sequence[Any],
    occupation: str,
    groups: Sequence[str],
    *,
    attr: str = "gender",
) -> dict[str, Any]:
    """Median article length per group in one relevant set.

    Answers the prior question: is there a length difference to control for at
    all? If the medians match, length cannot be the explanation and the tercile
    analysis is only a confirmation.
    """
    by_person: dict[str, tuple[str, int]] = {}
    for chunk in store_chunks:
        if not in_relevant_set(chunk.attrs, occupation):
            continue
        label = chunk.attrs.get(attr)
        if label is None:
            continue
        by_person[chunk.doc_id] = (str(label), int(chunk.attrs.get("n_chars", 0)))

    out: dict[str, Any] = {"n_people": len(by_person), "median_chars": {}, "n": {}}
    for group in groups:
        lengths = [n for g, n in by_person.values() if g == group]
        out["median_chars"][group] = float(np.median(lengths)) if lengths else None
        out["n"][group] = len(lengths)

    medians = [v for v in out["median_chars"].values() if v is not None]
    out["median_gap_chars"] = (max(medians) - min(medians)) if medians else 0.0
    return out


def tercile_edges(lengths: Sequence[int]) -> tuple[float, float]:
    """The two cut points that split `lengths` into terciles."""
    array = np.asarray(list(lengths), dtype=np.float64)
    if array.size == 0:
        return (0.0, 0.0)
    return float(np.quantile(array, 1 / 3)), float(np.quantile(array, 2 / 3))


def tercile_of(n_chars: int, edges: tuple[float, float]) -> str:
    low, high = edges
    if n_chars <= low:
        return "short"
    return "medium" if n_chars <= high else "long"


def amplification_by_length(
    runs: Sequence[tuple[str, list[RetrievedChunk]]],
    store_chunks: Sequence[Any],
    occupation: str,
    groups: Sequence[str],
    *,
    k: int,
    attr: str = "gender",
    seed: int = 0,
) -> dict[str, Any]:
    """Recompute A inside each length tercile of the relevant set.

    Both sides are restricted consistently: the pool for a tercile contains only
    people in that tercile, and the retrieved hits are filtered to the same
    tercile. Restricting one side and not the other would reintroduce exactly the
    population mismatch the main metric works to avoid.
    """
    people: dict[str, tuple[str, int]] = {}
    for chunk in store_chunks:
        if not in_relevant_set(chunk.attrs, occupation):
            continue
        label = chunk.attrs.get(attr)
        if label is not None:
            people[chunk.doc_id] = (str(label), int(chunk.attrs.get("n_chars", 0)))

    if not people:
        return {"terciles": {}, "edges": None}

    lengths = [n for _, n in people.values()]
    edges = tercile_edges(lengths)
    result: dict[str, Any] = {
        "edges_chars": list(edges),
        "k": k,
        "n_distinct_lengths": len(set(lengths)),
        "terciles": {},
    }

    for name in TERCILE_NAMES:
        pool = [g for g, n in people.values() if tercile_of(n, edges) == name]
        if not pool:
            continue
        restricted = [
            (
                query,
                [
                    hit
                    for hit in retrieved
                    if tercile_of(int(hit.chunk.attrs.get("n_chars", 0)), edges) == name
                ],
            )
            for query, retrieved in runs
        ]
        block = stratum_amplification(
            restricted, pool, groups, k=k, occupation=occupation, attr=attr, seed=seed
        )
        result["terciles"][name] = {
            "n_pool": block["n_pool"],
            "pool_counts": block["pool_counts"],
            "base_rate": block["base_rate"],
            "top_k_share": block["top_k_share"],
            "amplification": block["amplification"],
            "amplification_ci95": block["amplification_ci95"],
            "ci_suppressed": block["ci_suppressed"],
        }

    # A clumped length distribution cannot be cut into three non-empty parts.
    # Say so, rather than let a reader assume the missing tercile was measured
    # and found empty of hits.
    result["degenerate"] = len(result["terciles"]) < len(TERCILE_NAMES)
    if result["degenerate"]:
        result["degenerate_reason"] = (
            f"only {len(result['terciles'])} non-empty tercile(s): article lengths "
            f"take {len(set(lengths))} distinct value(s) across {len(lengths)} people"
        )
    return result
