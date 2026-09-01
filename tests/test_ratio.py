"""A = p_k/p0 carries the study's whole claim, so each property is pinned
against a case whose correct answer is known by construction."""

import pytest

from workshop_rag_forum.bias import ratio
from workshop_rag_forum.types import Chunk, RetrievedChunk

GROUPS = ["female", "male", "other"]


def retrieved(genders: list[str]) -> list[RetrievedChunk]:
    return [
        RetrievedChunk(
            chunk=Chunk(
                chunk_id=f"c{i}",
                doc_id=f"p{i}",
                text="t",
                source=f"dewiki:p{i}",
                attrs={"gender": g, "occupation": "Schauspiel"},
            ),
            score=1.0 - i * 0.01,
            rank=i,
        )
        for i, g in enumerate(genders)
    ]


def pool(n_female: int, n_male: int, n_other: int = 0) -> list[str]:
    return ["female"] * n_female + ["male"] * n_male + ["other"] * n_other


# ---- the ratio itself -----------------------------------------------------


def test_top_k_mirroring_the_pool_gives_A_of_one():
    # Pool 50/50, top-k 50/50 -> neutral.
    assert ratio.amplification(["female", "male"], pool(50, 50), "female") == 1.0


def test_over_representation_gives_A_above_one():
    # p0 = 0.5, p_k = 0.75 -> A = 1.5
    got = ratio.amplification(["male"] * 3 + ["female"], pool(50, 50), "male")
    assert got == pytest.approx(1.5)


def test_suppression_gives_A_below_one():
    got = ratio.amplification(["male"] * 3 + ["female"], pool(50, 50), "female")
    assert got == pytest.approx(0.5)


def test_A_is_scale_free_in_the_base_rate():
    """The point of a ratio: the same relative treatment scores the same A
    whether the group is half the pool or a twentieth of it."""
    balanced = ratio.amplification(
        ["female"] * 25 + ["male"] * 75, pool(50, 50), "female"
    )
    skewed = ratio.amplification(["female"] * 5 + ["male"] * 95, pool(5, 95), "female")
    assert balanced == pytest.approx(0.5)
    assert skewed == pytest.approx(1.0)  # 5% retrieved from a 5% pool is neutral
    # A share *difference* would have called both of these a 25-point gap.


def test_group_absent_from_the_pool_returns_none_not_infinity():
    assert ratio.amplification(["other"], pool(50, 50, 0), "other") is None


def test_group_in_pool_but_never_retrieved_is_zero_not_none():
    assert ratio.amplification(["male"] * 10, pool(50, 50), "female") == 0.0


def test_empty_retrieval_gives_zero():
    assert ratio.amplification([], pool(50, 50), "female") == 0.0


# ---- confidence intervals and their suppression ---------------------------


def test_ci_brackets_the_point_estimate():
    retrieved_groups = ["female"] * 30 + ["male"] * 70
    a = ratio.amplification(retrieved_groups, pool(500, 500), "female")
    interval = ratio.bootstrap_amplification(
        retrieved_groups, pool(500, 500), "female", seed=1
    )
    assert a is not None and interval is not None
    low, high = interval
    assert low <= a <= high


def test_ci_is_suppressed_for_a_group_below_the_threshold():
    """Section 13 of the outline: for tiny groups report n, not an interval.

    The threshold is on the group, not the pool: 'other' has 3 people inside a
    1003-person pool, which is exactly the non-binary case."""
    big_pool = pool(500, 500, 3)
    assert ratio.bootstrap_amplification(["other"], big_pool, "other", seed=0) is None
    # ...while the large groups in that same pool still get an interval.
    assert ratio.bootstrap_amplification(["female"], big_pool, "female", seed=0)


def test_ci_is_suppressed_when_the_group_is_absent():
    assert ratio.bootstrap_amplification(["male"] * 50, pool(0, 500), "female") is None


# ---- stratum aggregation --------------------------------------------------


def test_stratum_reports_base_rate_share_and_ratio_consistently():
    runs = [("Bekannte Schauspieler", retrieved(["male"] * 8 + ["female"] * 2))]
    out = ratio.stratum_amplification(runs, pool(500, 500), GROUPS, k=10)
    assert out["base_rate"]["female"] == pytest.approx(0.5)
    assert out["top_k_share"]["female"] == pytest.approx(0.2)
    assert out["amplification"]["female"] == pytest.approx(0.4)
    assert out["amplification"]["male"] == pytest.approx(1.6)


def test_stratum_respects_k_as_a_prefix():
    # First 4 are male, next 6 female: k=4 and k=10 must disagree.
    runs = [("q", retrieved(["male"] * 4 + ["female"] * 6))]
    at4 = ratio.stratum_amplification(runs, pool(500, 500), GROUPS, k=4)
    at10 = ratio.stratum_amplification(runs, pool(500, 500), GROUPS, k=10)
    assert at4["top_k_share"]["male"] == pytest.approx(1.0)
    assert at10["top_k_share"]["male"] == pytest.approx(0.4)


def test_unlabelled_results_are_excluded_from_p_k_and_reported():
    unlabelled = RetrievedChunk(
        chunk=Chunk("x", "x", "t", source="dewiki:x"), score=0.5, rank=2
    )
    runs = [("q", retrieved(["female", "male"]) + [unlabelled])]
    out = ratio.stratum_amplification(runs, pool(500, 500), GROUPS, k=3)
    # p_k is computed over the two labelled hits, not diluted by the third.
    assert out["top_k_share"]["female"] == pytest.approx(0.5)
    assert out["unlabelled_share"] == pytest.approx(1 / 3)


def test_stratum_records_why_a_ci_is_missing():
    runs = [("q", retrieved(["female", "male"]))]
    out = ratio.stratum_amplification(runs, pool(10, 10), GROUPS, k=2)
    assert out["amplification_ci95"]["female"] is None
    assert "n=10" in out["ci_suppressed"]["female"]  # 10 women < 30, and it says so
    assert out["ci_suppressed"]["other"] == "absent from pool"


def test_per_query_breakdown_separates_the_wordings():
    """Query wording is the section 10 variable; it must not be averaged away."""
    runs = [
        ("Bekannte Schauspieler", retrieved(["male"] * 10)),
        ("Bekannte Schauspielerinnen", retrieved(["female"] * 10)),
    ]
    out = ratio.stratum_amplification(runs, pool(500, 500), GROUPS, k=10)
    per_query = out["per_query_amplification"]
    assert per_query["Bekannte Schauspieler"]["male"] == pytest.approx(2.0)
    assert per_query["Bekannte Schauspielerinnen"]["male"] == pytest.approx(0.0)
    # Pooled over both wordings the effect cancels - which is why it is reported
    # per query as well as pooled.
    assert out["amplification"]["male"] == pytest.approx(1.0)


# ---- relevant-set filtering ----------------------------------------------


def occupational(gender: str, occupations: list[str], rank: int) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=f"c{rank}",
            doc_id=f"p{rank}",
            text="t",
            source="dewiki:x",
            attrs={"gender": gender, "occupations": occupations},
        ),
        score=1.0,
        rank=rank,
    )


def test_off_topic_hits_are_excluded_from_p_k():
    """Retrieval runs over the whole corpus, so an actor query returns
    footballers too. Counting them in p_k while p0 covers only actors would
    compare two different populations."""
    runs = [
        (
            "Bekannte Schauspieler",
            [
                occupational("female", ["Schauspiel"], 0),
                occupational("male", ["Fußball"], 1),  # off-topic
                occupational("male", ["Fußball"], 2),  # off-topic
            ],
        )
    ]
    out = ratio.stratum_amplification(
        runs, pool(500, 500), GROUPS, k=3, occupation="Schauspiel"
    )
    assert out["n_in_relevant_set"] == 1
    assert out["off_topic_share"] == pytest.approx(2 / 3)
    # The single on-topic hit is a woman -> p_k = 1.0 against p0 = 0.5.
    assert out["amplification"]["female"] == pytest.approx(2.0)


def test_multi_valued_occupations_count_in_every_stratum_they_belong_to():
    both = occupational("female", ["Schauspiel", "Politik"], 0)
    for occupation in ("Schauspiel", "Politik"):
        out = ratio.stratum_amplification(
            [("q", [both])], pool(500, 500), GROUPS, k=1, occupation=occupation
        )
        assert out["n_in_relevant_set"] == 1, occupation


def test_no_occupation_filter_keeps_everything():
    runs = [("q", [occupational("female", ["Fußball"], 0)])]
    out = ratio.stratum_amplification(runs, pool(500, 500), GROUPS, k=1)
    assert out["off_topic_share"] == 0.0
    assert out["n_in_relevant_set"] == 1
