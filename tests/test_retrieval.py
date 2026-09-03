"""Retrieval, reranking, generation and the pipeline.

Coverage for these was lost when the synthetic-probe test module was removed
during the pivot to the Wikidata study; this restores it.
"""

import pytest

from workshop_rag_forum.embedding import HashEmbedder
from workshop_rag_forum.generation import (
    EchoGenerator,
    build_prompt,
    format_context,
    parse_citations,
)
from workshop_rag_forum.pipeline import RagPipeline
from workshop_rag_forum.retrieval import (
    DenseRetriever,
    DetGreedyRetriever,
    MMRRetriever,
    rerank_detgreedy,
)
from workshop_rag_forum.store import VectorStore
from workshop_rag_forum.types import Chunk, RetrievedChunk

GROUPS = ["female", "male"]


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


# ---- dense retrieval ------------------------------------------------------


def test_dense_returns_k_hits_ranked_by_descending_score():
    results = DenseRetriever(corpus(), HashEmbedder(dim=64)).retrieve("Theater", k=5)
    assert [r.rank for r in results] == [0, 1, 2, 3, 4]
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_dense_clamps_k_to_corpus_size():
    assert len(DenseRetriever(corpus(), HashEmbedder(dim=64)).retrieve("x", k=99)) == 12


# ---- MMR ------------------------------------------------------------------


def test_mmr_returns_k_distinct_chunks_with_contiguous_ranks():
    store = corpus()
    results = MMRRetriever(store, HashEmbedder(dim=64), lambda_=0.3, pool=10).retrieve(
        "Theater", k=4
    )
    assert len({r.chunk.chunk_id for r in results}) == 4
    assert [r.rank for r in results] == [0, 1, 2, 3]


def test_mmr_rejects_lambda_outside_the_unit_interval():
    with pytest.raises(ValueError, match="lambda_"):
        MMRRetriever(corpus(), HashEmbedder(dim=64), lambda_=1.5)


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


# ---- citations and prompting ---------------------------------------------


def test_parse_citations_dedupes_and_orders_by_appearance():
    assert parse_citations("see [3] and [1], again [3]", n_contexts=5) == [2, 0]


def test_parse_citations_drops_hallucinated_references():
    assert parse_citations("as shown in [9] and [2]", n_contexts=3) == [1]
    assert parse_citations("no citations here", n_contexts=3) == []


def test_context_is_numbered_from_one():
    contexts = DenseRetriever(corpus(), HashEmbedder(dim=64)).retrieve("Theater", k=2)
    rendered = format_context(contexts)
    assert "[1]" in rendered and "[2]" in rendered and "[0]" not in rendered
    assert "Theater" in build_prompt("Wer?", contexts)


# ---- pipeline -------------------------------------------------------------


def test_pipeline_without_a_generator_refuses_to_answer():
    pipeline = RagPipeline(DenseRetriever(corpus(), HashEmbedder(dim=64)))
    with pytest.raises(RuntimeError, match="no generator"):
        pipeline.answer("Wer?")


def test_pipeline_answer_uses_a_fixed_context_instead_of_retrieving():
    store = corpus()
    pipeline = RagPipeline(
        DenseRetriever(store, HashEmbedder(dim=64)), EchoGenerator(2), top_k=3
    )
    fixed = pipeline.retrieve("Theater", k=5)
    answer = pipeline.answer("Wer?", contexts=fixed)
    assert answer.contexts == fixed
    assert answer.cited_ranks == [0, 1]
    assert [c.rank for c in answer.cited_contexts] == [0, 1]


def test_pipeline_name_records_every_component():
    pipeline = RagPipeline(
        DenseRetriever(corpus(), HashEmbedder(dim=64)), EchoGenerator(2), top_k=7
    )
    assert "dense" in pipeline.name and "k=7" in pipeline.name
