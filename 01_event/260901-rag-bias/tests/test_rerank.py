"""DetGreedy, the fairness-aware reranker behind the study's trade-off sweep."""

import pytest
from rag_bias.rerank import DetGreedyRetriever, rerank_detgreedy

from workshop_rag_forum.embedding import HashEmbedder
from workshop_rag_forum.store import VectorStore
from workshop_rag_forum.types import Chunk, RetrievedChunk


def corpus() -> VectorStore:
    chunks = [
        Chunk(
            chunk_id=f"c{i}",
            doc_id=f"p{i}",
            text=f"Person {i} ist Schauspieler und arbeitet am Theater {i % 3}",
            source=f"dewiki:P{i}",
            title=f"Person {i}",
            attrs={
                "gender": "female" if i % 2 else "male",
                "occupations": ["Schauspiel"],
                "n_chars": 100 + i * 10,
            },
        )
        for i in range(12)
    ]
    return VectorStore.build(chunks, HashEmbedder(dim=64))


def hit(gender: str, rank: int, score: float) -> RetrievedChunk:
    return RetrievedChunk(
        chunk=Chunk(
            chunk_id=f"c{rank}",
            doc_id=f"p{rank}",
            text="t",
            source="dewiki:x",
            attrs={"gender": gender, "occupations": ["Schauspiel"]},
        ),
        score=score,
        rank=rank,
    )


# ---- DetGreedy ------------------------------------------------------------


def test_detgreedy_enforces_the_target_in_every_prefix():
    """The prefix property is the point: a top-10 that is only fair at rank 100
    is not fair to anyone reading the first page."""
    # All men rank above all women by score.
    candidates = [hit("male", i, 1.0 - i * 0.01) for i in range(10)]
    candidates += [hit("female", 10 + i, 0.5 - i * 0.01) for i in range(10)]
    out = rerank_detgreedy(candidates, {"female": 0.5, "male": 0.5}, k=10)

    assert len(out) == 10
    for prefix in range(2, 11):
        women = sum(1 for h in out[:prefix] if h.chunk.attrs["gender"] == "female")
        # floor(prefix * 0.5) is the guaranteed minimum at each position.
        assert women >= prefix // 2, f"prefix {prefix} had only {women} women"


def test_detgreedy_leaves_an_already_matching_ranking_alone():
    candidates = [
        hit("female" if i % 2 else "male", i, 1.0 - i * 0.01) for i in range(10)
    ]
    out = rerank_detgreedy(candidates, {"female": 0.5, "male": 0.5}, k=10)
    assert [h.chunk.doc_id for h in out] == [h.chunk.doc_id for h in candidates]


def test_detgreedy_renumbers_ranks_to_the_new_order():
    candidates = [hit("male", i, 1.0 - i * 0.01) for i in range(4)]
    candidates += [hit("female", 4 + i, 0.5) for i in range(4)]
    out = rerank_detgreedy(candidates, {"female": 0.5, "male": 0.5}, k=6)
    assert [h.rank for h in out] == [0, 1, 2, 3, 4, 5]


def test_detgreedy_cannot_exceed_available_candidates():
    candidates = [hit("male", i, 1.0 - i * 0.01) for i in range(3)]
    out = rerank_detgreedy(candidates, {"female": 0.5, "male": 0.5}, k=10)
    assert len(out) == 3  # no women exist to promote


def test_detgreedy_normalises_targets_so_counts_work_too():
    store = corpus()
    a = DetGreedyRetriever(
        store, HashEmbedder(dim=64), targets={"female": 1, "male": 1}
    )
    b = DetGreedyRetriever(
        store, HashEmbedder(dim=64), targets={"female": 0.5, "male": 0.5}
    )
    assert a.targets == b.targets


def test_detgreedy_rejects_degenerate_targets():
    store, embedder = corpus(), HashEmbedder(dim=64)
    with pytest.raises(ValueError, match="non-negative"):
        DetGreedyRetriever(store, embedder, targets={"female": -1.0, "male": 1.0})
    with pytest.raises(ValueError, match="sum to zero"):
        DetGreedyRetriever(store, embedder, targets={"female": 0.0, "male": 0.0})


def test_detgreedy_retriever_satisfies_the_protocol_end_to_end():
    results = DetGreedyRetriever(
        corpus(), HashEmbedder(dim=64), targets={"female": 0.5, "male": 0.5}
    ).retrieve("Theater", k=6)
    assert len(results) == 6
    assert [r.rank for r in results] == [0, 1, 2, 3, 4, 5]
    assert (
        "detgreedy"
        in DetGreedyRetriever(
            corpus(), HashEmbedder(dim=64), targets={"female": 0.5, "male": 0.5}
        ).name
    )
