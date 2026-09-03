"""Retrieval bias measurement.

* `ratio`     the headline metric A = p_k/p0 and its refusal rules
* `quality`   nDCG against binary occupation relevance, to price an intervention
* `covariate` article length controlled by tercile stratification
* `study`     runs all of it across strata and k values, writes the results file
"""

from .covariate import amplification_by_length, length_profile, tercile_of
from .quality import dcg, ndcg_at_k, relevance
from .ratio import (
    MIN_N_FOR_CI,
    amplification,
    bootstrap_amplification,
    in_relevant_set,
    stratum_amplification,
)
from .study import (
    dedupe_by_person,
    pool_groups,
    print_summary,
    run_study,
    tradeoff_curve,
    write_results,
)

__all__ = [
    "MIN_N_FOR_CI",
    "amplification",
    "amplification_by_length",
    "bootstrap_amplification",
    "dcg",
    "dedupe_by_person",
    "in_relevant_set",
    "length_profile",
    "ndcg_at_k",
    "pool_groups",
    "print_summary",
    "relevance",
    "run_study",
    "stratum_amplification",
    "tercile_of",
    "tradeoff_curve",
    "write_results",
]
