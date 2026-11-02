"""Splitting documents into retrievable chunks.

Unlike the ad-hoc splitter in the turbovec meeting, this one never silently drops
text: a window that exceeds the character cap is split further rather than
truncated, and consecutive windows overlap so a fact straddling a boundary stays
retrievable from both sides.
"""

from __future__ import annotations

from collections.abc import Iterable

from .types import Chunk, Document


def split_words(
    text: str,
    *,
    n_words: int = 90,
    overlap_words: int = 20,
    max_chars: int = 450,
) -> list[str]:
    """Split `text` into overlapping word windows, capped at `max_chars`.

    `max_chars` is a guard against the embedding endpoint's per-input token limit.
    An over-long window is broken into further pieces on a word boundary instead
    of being cut off, so no source text is lost.
    """
    if n_words <= 0:
        raise ValueError("n_words must be positive")
    if not 0 <= overlap_words < n_words:
        raise ValueError("overlap_words must be >= 0 and < n_words")

    words = text.split()
    if not words:
        return []

    step = n_words - overlap_words
    windows: list[str] = []
    for start in range(0, len(words), step):
        window = words[start : start + n_words]
        if window:
            windows.extend(_cap_chars(window, max_chars))
        if start + n_words >= len(words):
            break  # the final window already reached the end
    return windows


def _cap_chars(words: list[str], max_chars: int) -> list[str]:
    """Join `words`, breaking into several strings if the cap is exceeded."""
    pieces: list[str] = []
    current: list[str] = []
    length = 0
    for word in words:
        # +1 for the joining space, only once `current` is non-empty.
        added = len(word) + (1 if current else 0)
        if current and length + added > max_chars:
            pieces.append(" ".join(current))
            current, length = [], 0
            added = len(word)
        current.append(word)
        length += added
    if current:
        pieces.append(" ".join(current))
    # A single word longer than the cap still has to be cut; hard-wrap it.
    return [p for piece in pieces for p in _hard_wrap(piece, max_chars)]


def _hard_wrap(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    return [text[i : i + max_chars] for i in range(0, len(text), max_chars)]


def chunk_document(
    doc: Document,
    *,
    n_words: int = 90,
    overlap_words: int = 20,
    max_chars: int = 450,
) -> list[Chunk]:
    """Chunk one document, propagating its provenance and attributes."""
    texts = split_words(
        doc.text, n_words=n_words, overlap_words=overlap_words, max_chars=max_chars
    )
    return [
        Chunk(
            chunk_id=f"{doc.doc_id}#{i}",
            doc_id=doc.doc_id,
            text=text,
            source=doc.source,
            title=doc.title,
            ordinal=i,
            attrs=dict(doc.attrs),
        )
        for i, text in enumerate(texts)
    ]


def chunk_documents(
    docs: Iterable[Document],
    *,
    n_words: int = 90,
    overlap_words: int = 20,
    max_chars: int = 450,
) -> list[Chunk]:
    return [
        chunk
        for doc in docs
        for chunk in chunk_document(
            doc, n_words=n_words, overlap_words=overlap_words, max_chars=max_chars
        )
    ]
