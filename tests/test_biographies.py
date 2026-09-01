"""Corpus construction. No network: populations are passed in directly."""

import pytest

from workshop_rag_forum import biographies as bio
from workshop_rag_forum.bias.study import pool_groups
from workshop_rag_forum.chunking import chunk_documents
from workshop_rag_forum.embedding import HashEmbedder
from workshop_rag_forum.store import VectorStore


def population(n_female: int, n_male: int, n_other: int = 0) -> list[dict[str, str]]:
    people = []
    for group, count in (("female", n_female), ("male", n_male), ("other", n_other)):
        for i in range(count):
            people.append(
                {
                    "qid": f"Q{group}{i}",
                    "title": f"{group} {i}",
                    "gender": group,
                    "occupation": "Schauspiel",
                    "occupation_qid": "Q33999",
                }
            )
    return people


def test_base_rates_are_population_shares():
    rates = bio.base_rates(population(30, 70))
    assert rates["female"] == pytest.approx(0.3)
    assert rates["male"] == pytest.approx(0.7)
    assert rates["other"] == pytest.approx(0.0)


def test_variant_R_preserves_the_real_split():
    sample = bio.sample_population(population(300, 700), n=200, variant="R", seed=0)
    assert len(sample) == 200
    share = sum(1 for p in sample if p["gender"] == "female") / len(sample)
    assert share == pytest.approx(0.3, abs=0.08)  # sampling noise at n=200


def test_variant_K_equalises_female_and_male():
    sample = bio.sample_population(population(300, 700), n=200, variant="K", seed=0)
    counts = {g: sum(1 for p in sample if p["gender"] == g) for g in bio.GROUPS}
    assert counts["female"] == counts["male"]
    assert counts["female"] > 0


def test_variant_K_cannot_invent_people_it_does_not_have():
    # Only 10 women exist; K must not fabricate a 100/100 split.
    sample = bio.sample_population(population(10, 700), n=200, variant="K", seed=0)
    counts = {g: sum(1 for p in sample if p["gender"] == g) for g in bio.GROUPS}
    assert counts["female"] == counts["male"] == 10


def test_sampling_is_deterministic_under_a_seed():
    a = bio.sample_population(population(300, 700), n=50, variant="R", seed=7)
    b = bio.sample_population(population(300, 700), n=50, variant="R", seed=7)
    assert [p["qid"] for p in a] == [p["qid"] for p in b]


def test_unknown_variant_is_rejected():
    with pytest.raises(ValueError, match="unknown variant"):
        bio.sample_population(population(10, 10), n=5, variant="Z")


def test_short_articles_are_dropped():
    people = population(1, 1)
    extracts = {"female 0": "x" * 500, "male 0": "too short"}
    docs = bio.build_documents(people, extracts, variant="R", min_chars=200)
    assert [d.title for d in docs] == ["female 0"]
    assert docs[0].attrs["gender"] == "female"
    assert docs[0].attrs["occupation"] == "Schauspiel"


def test_pool_counts_people_not_chunks():
    """A long biography split into many chunks must count once towards p0."""
    people = population(1, 1)
    extracts = {"female 0": "wort " * 400, "male 0": "wort " * 40}
    docs = bio.build_documents(people, extracts, variant="R")
    chunks = chunk_documents(docs, n_words=50, overlap_words=0)
    assert len(chunks) > 2  # the long article really did split
    store = VectorStore.build(chunks, HashEmbedder(dim=32))
    assert sorted(pool_groups(store, "Schauspiel")) == ["female", "male"]
