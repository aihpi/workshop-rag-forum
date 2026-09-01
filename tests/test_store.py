from pathlib import Path

import numpy as np
import pytest

from workshop_rag_forum.embedding import HashEmbedder, l2_normalise
from workshop_rag_forum.store import VectorStore
from workshop_rag_forum.types import Chunk


def make_chunks(n: int = 6) -> list[Chunk]:
    return [
        Chunk(
            chunk_id=f"c{i}",
            doc_id=f"d{i}",
            text=f"passage number {i} about topic {i % 2}",
            source=f"src{i % 3}",
            attrs={"group": "women" if i % 2 else "men", "valence": i % 3 - 1},
        )
        for i in range(n)
    ]


def test_build_keeps_text_and_vectors_aligned():
    chunks = make_chunks()
    store = VectorStore.build(chunks, HashEmbedder(dim=64))
    assert len(store) == len(chunks) == len(store.vectors)
    assert store.dim == 64


def test_mismatched_lengths_are_rejected():
    with pytest.raises(ValueError, match="row-aligned"):
        VectorStore(make_chunks(3), np.zeros((2, 8), dtype=np.float32))


def test_search_returns_exact_cosine_order():
    chunks = make_chunks(5)
    embedder = HashEmbedder(dim=32)
    store = VectorStore.build(chunks, embedder)
    query = embedder.embed([chunks[3].text])
    scores, indices = store.search(query, k=3)
    assert indices[0][0] == 3  # a chunk is its own nearest neighbour
    assert scores[0][0] == pytest.approx(1.0, abs=1e-5)
    assert list(scores[0]) == sorted(scores[0], reverse=True)


def test_search_rejects_wrong_dimensionality():
    store = VectorStore.build(make_chunks(3), HashEmbedder(dim=32))
    with pytest.raises(ValueError, match="different embedding model"):
        store.search(np.zeros((1, 16), dtype=np.float32), k=1)


def test_search_k_larger_than_store_is_clamped():
    store = VectorStore.build(make_chunks(3), HashEmbedder(dim=32))
    scores, indices = store.search(store.vectors[:1], k=99)
    assert indices.shape == scores.shape == (1, 3)


def test_round_trip_through_disk(tmp_path: Path):
    chunks = make_chunks(7)
    store = VectorStore.build(chunks, HashEmbedder(dim=32))
    store.save(tmp_path)
    loaded = VectorStore.load(tmp_path)

    assert len(loaded) == len(store)
    assert loaded.embedder_name == "hash-32"
    np.testing.assert_allclose(loaded.vectors, store.vectors, atol=1e-6)
    assert [c.text for c in loaded.chunks] == [c.text for c in chunks]
    # attrs survive with their types intact, which the metrics depend on.
    assert loaded.chunks[1].attrs == chunks[1].attrs


def test_load_missing_store_explains_itself(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="ingest"):
        VectorStore.load(tmp_path / "nope")


def test_add_extends_an_existing_store():
    embedder = HashEmbedder(dim=32)
    store = VectorStore.build(make_chunks(3), embedder)
    store.add(make_chunks(2), embedder)
    assert len(store) == 5 == len(store.vectors)


def test_hash_embedder_is_deterministic_and_normalised():
    embedder = HashEmbedder(dim=48)
    first = embedder.embed(["hello world", "something else"])
    second = embedder.embed(["hello world", "something else"])
    np.testing.assert_array_equal(first, second)
    np.testing.assert_allclose(np.linalg.norm(first, axis=1), 1.0, atol=1e-6)


def test_l2_normalise_survives_a_zero_vector():
    out = l2_normalise(np.zeros((1, 4), dtype=np.float32))
    assert np.all(np.isfinite(out))
