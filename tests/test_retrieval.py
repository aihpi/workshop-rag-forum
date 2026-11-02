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
    MMRRetriever,
)
from workshop_rag_forum.store import VectorStore
from workshop_rag_forum.types import Chunk


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
