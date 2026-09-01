"""Secondary diagnostics: concentration helpers."""

import math

import pytest

from workshop_rag_forum.bias import metrics
from workshop_rag_forum.types import Chunk, RetrievedChunk


def retrieved(sources: list[str]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk=Chunk(f"c{i}", f"d{i}", "text", source=src), score=1.0, rank=i
        )
        for i, src in enumerate(sources)
    ]


def test_even_source_spread_gives_effective_count_equal_to_source_count():
    runs = [("q", retrieved([f"s{i}" for i in range(4)]))]
    result = metrics.source_concentration(runs, rank_weighted=False)
    assert result["effective_sources"] == pytest.approx(4.0)
    assert result["gini"] == pytest.approx(0.0)
    assert result["top_source_share"] == pytest.approx(0.25)


def test_single_source_monopoly_collapses_the_effective_count():
    runs = [("q", retrieved(["s1"] * 4))]
    result = metrics.source_concentration(runs, rank_weighted=False)
    assert result["effective_sources"] == pytest.approx(1.0)
    assert result["top_source_share"] == pytest.approx(1.0)


def test_coverage_compares_against_the_whole_corpus():
    runs = [("q", retrieved(["s1"]))]
    result = metrics.source_concentration(
        runs, corpus_sources=["s1", "s2", "s3", "s4"], rank_weighted=False
    )
    assert result["sources_available"] == 4
    assert result["coverage"] == pytest.approx(0.25)


def test_gini_bounds():
    assert metrics.gini([1, 1, 1, 1]) == pytest.approx(0.0)
    assert metrics.gini([0, 0, 0, 1]) == pytest.approx(0.75)
    assert metrics.gini([]) == 0.0


def test_normalised_entropy_bounds():
    assert metrics.normalised_entropy([0.5, 0.5]) == pytest.approx(1.0)
    assert metrics.normalised_entropy([1.0, 0.0]) == pytest.approx(0.0)


def test_rank_weight_decreases_monotonically():
    weights = [metrics.rank_weight(i) for i in range(5)]
    assert weights == sorted(weights, reverse=True)
    assert weights[0] == pytest.approx(1.0)


def test_bootstrap_ci_brackets_the_mean():
    samples = [0.1, 0.2, 0.3, 0.4, 0.5]
    low, high = metrics.bootstrap_ci(samples, seed=1)
    assert low <= sum(samples) / len(samples) <= high


def test_bootstrap_ci_handles_degenerate_inputs():
    assert all(math.isnan(v) for v in metrics.bootstrap_ci([]))
    assert metrics.bootstrap_ci([0.7]) == (0.7, 0.7)
