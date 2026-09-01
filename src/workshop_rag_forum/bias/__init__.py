"""Retrieval bias measurement.

`ratio` holds the headline metric A = p_k/p0, `study` runs it across occupation
strata and k values, and `metrics` keeps the secondary source-concentration
diagnostics.
"""

from .metrics import gini, herfindahl, normalised_entropy, source_concentration
from .ratio import (
    MIN_N_FOR_CI,
    amplification,
    bootstrap_amplification,
    stratum_amplification,
)
from .study import pool_groups, print_summary, run_study, write_results

__all__ = [
    "MIN_N_FOR_CI",
    "amplification",
    "bootstrap_amplification",
    "gini",
    "herfindahl",
    "normalised_entropy",
    "pool_groups",
    "print_summary",
    "run_study",
    "source_concentration",
    "stratum_amplification",
    "write_results",
]
