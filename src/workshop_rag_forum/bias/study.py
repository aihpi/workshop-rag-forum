"""Runs the retrieval bias study and writes a results document.

One run covers every occupation stratum x every query phrasing, and reports A at
each requested k. Retrieval happens once per query at the largest k; the smaller
k values are prefixes of that same ranking, so k = 10 and k = 100 describe the
same run rather than two runs that might differ for unrelated reasons.
"""

from __future__ import annotations

import json
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ..biographies import GROUPS, Occupation
from ..retrieval import Retriever
from ..store import VectorStore
from .ratio import stratum_amplification


def pool_groups(
    store: VectorStore, occupation_label: str, *, attr: str = "gender"
) -> list[str]:
    """Gender labels of every corpus person in one occupation's relevant set.

    Deduplicated by person: a biography split into several chunks must not count
    its author more than once, or long articles would silently inflate p0.
    """
    from .ratio import in_relevant_set

    seen: dict[str, str] = {}
    for chunk in store.chunks:
        if not in_relevant_set(chunk.attrs, occupation_label):
            continue
        label = chunk.attrs.get(attr)
        if label is not None:
            seen[chunk.doc_id] = str(label)
    return list(seen.values())


def _dedupe_by_person(retrieved: list[Any]) -> list[Any]:
    """Collapse multiple chunks of one biography to its best-ranked chunk.

    Top-k is meant to be k *people*. Without this, one long article occupying
    three slots would be counted as three retrievals of that person's group.
    """
    seen: set[str] = set()
    out = []
    for item in retrieved:
        if item.chunk.doc_id in seen:
            continue
        seen.add(item.chunk.doc_id)
        out.append(item)
    return out


def run_study(
    store: VectorStore,
    retriever: Retriever,
    occupations: list[Occupation],
    *,
    ks: list[int] | None = None,
    variant: str = "R",
    seed: int = 0,
    groups: list[str] | None = None,
) -> dict[str, Any]:
    ks = sorted(ks or [10, 100])
    groups = groups or GROUPS
    max_k = max(ks)

    strata: list[dict[str, Any]] = []
    for occupation in occupations:
        pool = pool_groups(store, occupation.label)
        if not pool:
            continue
        # Retrieve deep enough that the largest k survives person-deduplication.
        runs = [
            (query, _dedupe_by_person(retriever.retrieve(query, k=max_k * 3)))
            for query in occupation.queries
        ]
        strata.append(
            {
                "occupation": occupation.label,
                "occupation_qid": occupation.qid,
                "queries": occupation.queries,
                "by_k": {
                    str(k): stratum_amplification(
                        runs,
                        pool,
                        groups,
                        k=k,
                        occupation=occupation.label,
                        seed=seed,
                    )
                    for k in ks
                },
            }
        )

    return {
        "created": datetime.now(UTC).isoformat(timespec="seconds"),
        "variant": variant,
        "config": {
            "retriever": retriever.name,
            "embedder": store.embedder_name,
            "ks": ks,
            "seed": seed,
            "groups": groups,
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
        print(f"\n  {stratum['occupation']}  (pool n={block['n_pool']})")
        for group in results["config"]["groups"]:
            a = block["amplification"][group]
            if a is None:
                print(f"    {group:8s} —  {block['ci_suppressed'].get(group, '')}")
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
