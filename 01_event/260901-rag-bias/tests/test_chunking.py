from workshop_rag_forum.chunking import chunk_document, split_words
from workshop_rag_forum.types import Document


def test_split_preserves_every_word():
    text = " ".join(f"w{i}" for i in range(500))
    chunks = split_words(text, n_words=50, overlap_words=10, max_chars=10_000)
    # Overlap means words repeat, but none may go missing.
    seen = {word for chunk in chunks for word in chunk.split()}
    assert seen == set(text.split())


def test_windows_overlap_by_the_requested_amount():
    text = " ".join(f"w{i}" for i in range(100))
    chunks = split_words(text, n_words=20, overlap_words=5, max_chars=10_000)
    first, second = chunks[0].split(), chunks[1].split()
    assert first[-5:] == second[:5]


def test_char_cap_splits_rather_than_truncates():
    text = " ".join("abcdefgh" for _ in range(50))
    chunks = split_words(text, n_words=50, overlap_words=0, max_chars=40)
    assert all(len(c) <= 40 for c in chunks)
    # The turbovec pipeline dropped the tail here; this one must not.
    assert sum(len(c.split()) for c in chunks) == 50


def test_single_word_longer_than_cap_is_hard_wrapped():
    chunks = split_words("x" * 250, n_words=10, overlap_words=0, max_chars=100)
    assert [len(c) for c in chunks] == [100, 100, 50]


def test_empty_text_yields_no_chunks():
    assert split_words("   ") == []


def test_chunk_document_propagates_provenance():
    doc = Document(
        doc_id="d1",
        text=" ".join(f"w{i}" for i in range(200)),
        source="probe",
        title="T",
        attrs={"group": "women"},
    )
    chunks = chunk_document(doc, n_words=50, overlap_words=0, max_chars=10_000)
    assert len(chunks) == 4
    assert [c.chunk_id for c in chunks] == ["d1#0", "d1#1", "d1#2", "d1#3"]
    assert all(c.attrs == {"group": "women"} and c.source == "probe" for c in chunks)
    # attrs must be copied, not shared, or one edit would rewrite every chunk.
    chunks[0].attrs["group"] = "men"
    assert chunks[1].attrs["group"] == "women"
