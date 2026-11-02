"""The 260901 retrieval bias study, built on the shared `workshop_rag_forum` pipeline.

* `biographies` the corpus: German Wikipedia biographies labelled from Wikidata
* `bias`        the metric A = p_k/p0, nDCG, the length covariate and the runner
* `rerank`      DetGreedy, the fairness-aware reranker the trade-off sweep uses
* `cli`         the `rag-bias` command, deliberately not re-exported here
"""

from .biographies import (
    DEFAULT_OCCUPATIONS,
    GROUPS,
    Occupation,
    base_rates,
    build_documents,
    fetch_population,
    sample_population,
)
from .rerank import DetGreedyRetriever, rerank_detgreedy

__all__ = [
    "DEFAULT_OCCUPATIONS",
    "DetGreedyRetriever",
    "GROUPS",
    "Occupation",
    "base_rates",
    "build_documents",
    "fetch_population",
    "rerank_detgreedy",
    "sample_population",
]
