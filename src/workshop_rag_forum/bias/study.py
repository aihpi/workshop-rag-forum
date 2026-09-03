"""Runs the retrieval bias study and writes a results document.

One run covers every occupation stratum by every query phrasing, and reports A at
each requested k. Retrieval happens once per query at the largest k; the smaller
k values are prefixes of that same ranking, so k = 10 and k = 100 describe the
same run rather than two runs that might differ for unrelated reasons.

Four things are computed per stratum, from that single retrieval:

* **A = p_k/p0** at each k, the headline (see `ratio`).
* **nDCG** at each k, so a fairness intervention can be priced (see `quality`).
* **A within length terciles**, controlling for article length (see `covariate`).
* **A against nDCG** as DetGreedy is swept from off to full parity.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from ..biographies import GROUPS, Occupation
from ..retrieval import Retriever, rerank_detgreedy
from ..store import VectorStore
from ..types import RetrievedChunk
from .covariate import amplification_by_length, length_profile
from .quality import ndcg_at_k
from .ratio import in_relevant_set, stratum_amplification

# (query text, ranked hits) for one query phrasing.
Run = tuple[str, list[RetrievedChunk]]


def pool_groups(
    store: VectorStore, occupation_label: str, *, attr: str = "gender"
) -> list[str]:
    """Group labels of every corpus person in one occupation's relevant set.

    Deduplicated by person: a biography split into several chunks must not count
    its author more than once, or long articles would silently inflate p0.
    """
    seen: dict[str, str] = {}
    for chunk in store.chunks:
        if not in_relevant_set(chunk.attrs, occupation_label):
            continue
        label = chunk.attrs.get(attr)
        if label is not None:
            seen[chunk.doc_id] = str(label)
    return list(seen.values())


def dedupe_by_person(retrieved: list[RetrievedChunk]) -> list[RetrievedChunk]:
    """Collapse multiple chunks of one biography to its best-ranked chunk.

    Top-k is meant to be k *people*. Without this, one long article occupying
    three slots would be counted as three retrievals of that person's group.
    Ranks are renumbered so positions stay contiguous after the collapse.
    """
    seen: set[str] = set()
    out: list[RetrievedChunk] = []
    for item in retrieved:
        if item.chunk.doc_id in seen:
            continue
        seen.add(item.chunk.doc_id)
        out.append(RetrievedChunk(chunk=item.chunk, score=item.score, rank=len(out)))
    return out


def tradeoff_curve(
    runs: list[Run],
    pool: list[str],
    groups: list[str],
    *,
    occupation: str,
    k: int,
    steps: int = 5,
    attr: str = "gender",
    seed: int = 0,
) -> list[dict[str, Any]]:
    """Sweep DetGreedy from "leave it alone" to "match the base rate exactly".

    At lambda = 0 the targets are the ranking's own observed composition, so
    DetGreedy has nothing to correct and returns essentially the input order. At
    lambda = 1 the targets are the corpus base rates p0, which is a request for
    A = 1. Intermediate values interpolate, tracing what each step towards parity
    costs in nDCG.

    Reranking is applied to rankings that were already fetched, so a whole curve
    costs no extra retrieval.
    """
    if not pool:
        return []
    base_rate = {g: pool.count(g) / len(pool) for g in groups}
    observed = stratum_amplification(
        runs, pool, groups, k=k, occupation=occupation, attr=attr, seed=seed
    )["top_k_share"]

    curve: list[dict[str, Any]] = []
    for step in range(steps + 1):
        lam = step / steps
        targets = {
            g: (1 - lam) * observed.get(g, 0.0) + lam * base_rate.get(g, 0.0)
            for g in groups
        }
        if sum(targets.values()) <= 0:
            continue
        reranked = [
            (query, rerank_detgreedy(hits, targets, k=k, attr=attr))
            for query, hits in runs
        ]
        block = stratum_amplification(
            reranked, pool, groups, k=k, occupation=occupation, attr=attr, seed=seed
        )
        curve.append(
            {
                "lambda": lam,
                "targets": targets,
                "amplification": block["amplification"],
                "top_k_share": block["top_k_share"],
                "ndcg": float(
                    np.mean([ndcg_at_k(hits, occupation, k=k) for _, hits in reranked])
                ),
            }
        )
    return curve


def run_study(
    store: VectorStore,
    retriever: Retriever,
    occupations: list[Occupation],
    *,
    ks: list[int] | None = None,
    variant: str = "R",
    seed: int = 0,
    groups: list[str] | None = None,
    tradeoff: bool = True,
    covariate: bool = True,
) -> dict[str, Any]:
    ks = sorted(ks or [10, 100])
    groups = groups or GROUPS
    max_k = max(ks)
    headline_k = ks[0]

    strata: list[dict[str, Any]] = []
    for occupation in occupations:
        pool = pool_groups(store, occupation.label)
        if not pool:
            continue
        # Retrieve deep enough that the largest k survives person-deduplication.
        runs: list[Run] = [
            (query, dedupe_by_person(retriever.retrieve(query, k=max_k * 3)))
            for query in occupation.queries
        ]
        # If dedupe left fewer people than the largest k, that k is not really
        # reached; record it rather than let a short ranking look like a result.
        shortest = min(len(hits) for _, hits in runs)

        stratum: dict[str, Any] = {
            "occupation": occupation.label,
            "occupation_qid": occupation.qid,
            "queries": occupation.queries,
            "n_distinct_people_retrieved": shortest,
            "k_fully_reached": [k for k in ks if k <= shortest],
            "ndcg": {
                str(k): float(
                    np.mean(
                        [ndcg_at_k(hits, occupation.label, k=k) for _, hits in runs]
                    )
                )
                for k in ks
            },
            "by_k": {
                str(k): stratum_amplification(
                    runs, pool, groups, k=k, occupation=occupation.label, seed=seed
                )
                for k in ks
            },
        }
        if covariate:
            stratum["length_profile"] = length_profile(
                store.chunks, occupation.label, groups
            )
            stratum["by_length_tercile"] = amplification_by_length(
                runs, store.chunks, occupation.label, groups, k=headline_k, seed=seed
            )
        if tradeoff:
            stratum["tradeoff"] = tradeoff_curve(
                runs, pool, groups, occupation=occupation.label, k=headline_k, seed=seed
            )
        strata.append(stratum)

    return {
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "variant": variant,
        "config": {
            "retriever": retriever.name,
            "embedder": store.embedder_name,
            "ks": ks,
            "seed": seed,
            "groups": groups,
            "tradeoff": tradeoff,
            "covariate": covariate,
        },
        "corpus": {
            "n_chunks": len(store),
            "n_people": len({c.doc_id for c in store.chunks}),
            "by_occupation": dict(
                Counter(
                    str(c.attrs.get("occupation"))
                    for c in store.chunks
                    if c.attrs.get("occupation")
                )
            ),
        },
        "strata": strata,
    }


def write_results(results: dict[str, Any], path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(results, indent=2, default=str))
    return path


def print_summary(results: dict[str, Any], headline_k: int = 10) -> None:
    key = str(headline_k)
    print(
        f"\nVariante {results['variant']} · {results['config']['retriever']} · "
        f"{results['corpus']['n_people']} people · A = p_k/p0 at k={headline_k}"
    )
    for stratum in results["strata"]:
        block = stratum["by_k"].get(key)
        if not block:
            continue
        ndcg = stratum.get("ndcg", {}).get(key)
        suffix = f" · nDCG={ndcg:.3f}" if ndcg is not None else ""
        print(f"\n  {stratum['occupation']}  (pool n={block['n_pool']}{suffix})")
        for group in results["config"]["groups"]:
            a = block["amplification"][group]
            if a is None:
                print(f"    {group:8s} -   {block['ci_suppressed'].get(group, '')}")
                continue
            ci = block["amplification_ci95"][group]
            span = (
                f"[{ci[0]:.2f}, {ci[1]:.2f}]"
                if ci
                else f"(no CI: {block['ci_suppressed'].get(group, '')})"
            )
            flag = (
                "  <-- suppressed"
                if a < 0.8
                else ("  <-- amplified" if a > 1.25 else "")
            )
            print(
                f"    {group:8s} p0={block['base_rate'][group]:.3f} "
                f"p_k={block['top_k_share'][group]:.3f}  A={a:.2f} {span}{flag}"
            )

        tercile = stratum.get("by_length_tercile") or {}
        if tercile.get("terciles"):
            cells = []
            for name, data in tercile["terciles"].items():
                value = data["amplification"].get(results["config"]["groups"][0])
                cells.append(
                    f"{name}={value:.2f}" if value is not None else f"{name}=-"
                )
            print(f"    A by article length: {'  '.join(cells)}")

        curve = stratum.get("tradeoff") or []
        if curve:
            first, last = curve[0], curve[-1]
            print(
                f"    DetGreedy: nDCG {first['ndcg']:.3f} -> {last['ndcg']:.3f} "
                f"for full parity"
            )
