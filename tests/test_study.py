"""The study runner, the length covariate and the nDCG trade-off."""

import pytest

from workshop_rag_forum.bias import covariate, quality, study
from workshop_rag_forum.biographies import Occupation
from workshop_rag_forum.embedding import HashEmbedder
from workshop_rag_forum.retrieval import DenseRetriever
from workshop_rag_forum.store import VectorStore
from workshop_rag_forum.types import Chunk, RetrievedChunk

GROUPS = ["female", "male", "other"]


def person(idx: int, gender: str, occupation: str, n_chars: int = 500) -> Chunk:
    return Chunk(
        chunk_id=f"c{idx}",
        doc_id=f"Q{idx}",
        text=f"Person {idx} ist {occupation} und sehr bekannt in {occupation}",
        source=f"dewiki:Person {idx}",
        title=f"Person {idx}",
        attrs={
            "gender": gender,
            "occupations": [occupation],
            "occupation": occupation,
            "n_chars": n_chars,
        },
    )


def store_of(chunks: list[Chunk]) -> VectorStore:
    return VectorStore.build(chunks, HashEmbedder(dim=64))


def hit(gender: str, rank: int, occupation: str = "Schauspiel", n_chars: int = 500):
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=f"h{rank}",
            doc_id=f"H{rank}",
            text="t",
            source="dewiki:x",
            attrs={"gender": gender, "occupations": [occupation], "n_chars": n_chars},
        ),
        score=1.0 - rank * 0.01,
        rank=rank,
    )


# ---- pooling and dedupe ---------------------------------------------------


def test_pool_counts_each_person_once_across_their_chunks():
    chunks = [person(0, "female", "Schauspiel"), person(1, "male", "Schauspiel")]
    # A second chunk of the same person must not be counted twice.
    extra = Chunk(
        chunk_id="c0b",
        doc_id="Q0",
        text="mehr",
        source="dewiki:Person 0",
        attrs=dict(chunks[0].attrs),
    )
    pool = study.pool_groups(store_of([*chunks, extra]), "Schauspiel")
    assert sorted(pool) == ["female", "male"]


def test_dedupe_keeps_the_best_ranked_chunk_and_renumbers():
    a1, a2 = hit("female", 0), hit("female", 1)
    a2 = RetrievedChunk(chunk=a1.chunk, score=0.5, rank=1)  # same person, worse rank
    b = hit("male", 2)
    out = study.dedupe_by_person([a1, a2, b])
    assert [h.chunk.doc_id for h in out] == [a1.chunk.doc_id, b.chunk.doc_id]
    assert [h.rank for h in out] == [0, 1]


# ---- nDCG -----------------------------------------------------------------


def test_ndcg_is_one_when_every_hit_is_on_topic():
    hits = [hit("female", i) for i in range(5)]
    assert quality.ndcg_at_k(hits, "Schauspiel", k=5) == pytest.approx(1.0)


def test_ndcg_is_zero_when_nothing_is_on_topic():
    hits = [hit("female", i, occupation="Fußball") for i in range(5)]
    assert quality.ndcg_at_k(hits, "Schauspiel", k=5) == 0.0


def test_ndcg_punishes_burying_the_relevant_hits():
    good = [hit("female", 0), hit("male", 1, occupation="Fußball")]
    bad = [hit("male", 0, occupation="Fußball"), hit("female", 1)]
    assert quality.ndcg_at_k(good, "Schauspiel", k=2) > quality.ndcg_at_k(
        bad, "Schauspiel", k=2
    )


# ---- length covariate -----------------------------------------------------


def test_length_profile_reports_the_median_gap_between_groups():
    chunks = [person(i, "female", "Schauspiel", n_chars=100) for i in range(4)]
    chunks += [person(10 + i, "male", "Schauspiel", n_chars=900) for i in range(4)]
    profile = covariate.length_profile(store_of(chunks).chunks, "Schauspiel", GROUPS)
    assert profile["median_chars"]["female"] == pytest.approx(100)
    assert profile["median_chars"]["male"] == pytest.approx(900)
    assert profile["median_gap_chars"] == pytest.approx(800)


def test_terciles_split_at_the_thirds():
    edges = covariate.tercile_edges([0, 100, 200, 300, 400, 500])
    assert covariate.tercile_of(0, edges) == "short"
    assert covariate.tercile_of(500, edges) == "long"


def test_length_stratification_neutralises_a_pure_length_effect():
    """If a retriever only prefers long articles, and one group's articles are
    longer, A is skewed overall but returns to parity inside a tercile, where
    every person has a comparable length."""
    # Women short, men long, with spread so the terciles are well defined.
    chunks = [person(i, "female", "Schauspiel", n_chars=100 + i * 5) for i in range(15)]
    chunks += [
        person(100 + i, "male", "Schauspiel", n_chars=800 + i * 5) for i in range(15)
    ]
    store = store_of(chunks)
    long_hits = [
        RetrievedChunk(chunk=c, score=1.0, rank=i)
        for i, c in enumerate(c for c in store.chunks if c.attrs["n_chars"] >= 800)
    ]
    result = covariate.amplification_by_length(
        [("q", long_hits)], store.chunks, "Schauspiel", GROUPS, k=10
    )
    assert not result["degenerate"]
    # In the "long" tercile every person is a man, so retrieving only men there
    # is exactly parity rather than amplification.
    assert result["terciles"]["long"]["amplification"]["male"] == pytest.approx(1.0)
    # Women are absent from that tercile, so their A is unanswerable, not zero.
    assert result["terciles"]["long"]["amplification"]["female"] is None


def test_clumped_lengths_report_a_degenerate_stratification():
    """Two distinct lengths cannot be cut into three terciles. That has to be
    visible, or a reader assumes the missing tercile was measured and empty."""
    chunks = [person(i, "female", "Schauspiel", n_chars=100) for i in range(10)]
    chunks += [person(100 + i, "male", "Schauspiel", n_chars=900) for i in range(10)]
    store = store_of(chunks)
    hits = [
        RetrievedChunk(chunk=c, score=1.0, rank=i) for i, c in enumerate(store.chunks)
    ]
    result = covariate.amplification_by_length(
        [("q", hits)], store.chunks, "Schauspiel", GROUPS, k=10
    )
    assert result["degenerate"]
    assert "2 distinct value(s)" in result["degenerate_reason"]


# ---- trade-off curve ------------------------------------------------------


def test_tradeoff_moves_amplification_towards_parity_and_prices_it():
    pool = ["female"] * 50 + ["male"] * 50
    # A ranking that is all men: A(female) = 0.
    runs = [
        (
            "q",
            [hit("male", i) for i in range(10)]
            + [hit("female", 10 + i) for i in range(10)],
        )
    ]
    curve = study.tradeoff_curve(
        runs, pool, ["female", "male"], occupation="Schauspiel", k=10, steps=4
    )
    assert [point["lambda"] for point in curve] == [0.0, 0.25, 0.5, 0.75, 1.0]
    assert curve[0]["amplification"]["female"] == pytest.approx(0.0)
    # Full parity brings women to their base rate.
    assert curve[-1]["amplification"]["female"] == pytest.approx(1.0, abs=0.15)
    # Every point carries the relevance cost of getting there.
    assert all("ndcg" in point for point in curve)


def test_tradeoff_on_an_empty_pool_returns_nothing():
    assert study.tradeoff_curve([], [], GROUPS, occupation="x", k=10) == []


# ---- end to end -----------------------------------------------------------


def test_run_study_produces_every_section():
    chunks = [person(i, "female", "Schauspiel", 200) for i in range(20)]
    chunks += [person(100 + i, "male", "Schauspiel", 800) for i in range(20)]
    store = store_of(chunks)
    occupations = [Occupation("Q33999", "Schauspiel", ["Bekannte Schauspieler"])]

    results = study.run_study(
        store,
        DenseRetriever(store, HashEmbedder(dim=64)),
        occupations,
        ks=[5, 10],
        variant="K",
    )

    assert results["variant"] == "K"
    assert results["corpus"]["n_people"] == 40
    stratum = results["strata"][0]
    for section in ("by_k", "ndcg", "length_profile", "by_length_tercile", "tradeoff"):
        assert stratum[section], f"missing {section}"
    assert set(stratum["by_k"]) == {"5", "10"}
    assert stratum["k_fully_reached"] == [5, 10]


def test_run_study_records_when_k_was_not_reached():
    chunks = [person(i, "female", "Schauspiel") for i in range(3)]
    store = store_of(chunks)
    results = study.run_study(
        store,
        DenseRetriever(store, HashEmbedder(dim=64)),
        [Occupation("Q1", "Schauspiel", ["q"])],
        ks=[10],
    )
    stratum = results["strata"][0]
    assert stratum["n_distinct_people_retrieved"] == 3
    assert stratum["k_fully_reached"] == []  # k=10 was never actually available


def test_run_study_can_skip_the_optional_sections():
    chunks = [person(i, "male", "Schauspiel") for i in range(6)]
    store = store_of(chunks)
    results = study.run_study(
        store,
        DenseRetriever(store, HashEmbedder(dim=64)),
        [Occupation("Q1", "Schauspiel", ["q"])],
        ks=[5],
        tradeoff=False,
        covariate=False,
    )
    assert "tradeoff" not in results["strata"][0]
    assert "by_length_tercile" not in results["strata"][0]


def test_run_study_skips_occupations_absent_from_the_corpus():
    store = store_of([person(0, "male", "Schauspiel")])
    results = study.run_study(
        store,
        DenseRetriever(store, HashEmbedder(dim=64)),
        [Occupation("Q2", "Fußball", ["q"])],
        ks=[5],
    )
    assert results["strata"] == []
