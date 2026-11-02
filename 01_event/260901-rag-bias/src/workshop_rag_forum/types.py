"""Core data types shared across the RAG pipeline.

Everything that crosses a module boundary is one of these. They are plain
dataclasses so they serialise to JSON/parquet without ceremony.

The `attrs` mapping on `Chunk` is what makes bias measurement possible:
biography chunks carry their Wikidata labels there, so the metrics read ground
truth rather than a classifier's guess.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

# Attribute keys the study reads off a chunk. Documents without them - anything
# that is not a labelled biography - are excluded from p_k rather than bucketed.
ATTR_GROUP = "gender"  # P21 bucket: "female" | "male" | "other"
ATTR_OCCUPATION = "occupation"  # P106 label; defines the relevant set per query


@dataclass(slots=True)
class Document:
    """A source document, before chunking."""

    doc_id: str
    text: str
    source: str = "unknown"
    title: str = ""
    attrs: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class Chunk:
    """A retrievable unit of text, carrying its provenance and labels."""

    chunk_id: str
    doc_id: str
    text: str
    source: str = "unknown"
    title: str = ""
    ordinal: int = 0
    attrs: dict[str, Any] = field(default_factory=dict)

    def to_row(self) -> dict[str, Any]:
        row = asdict(self)
        # Parquet round-trips a JSON-ish column badly; keep attrs flat and typed.
        row["attrs"] = dict(self.attrs)
        return row


@dataclass(slots=True)
class RetrievedChunk:
    """A chunk returned by a retriever, with its similarity score and rank."""

    chunk: Chunk
    score: float
    rank: int

    @property
    def group(self) -> str | None:
        value = self.chunk.attrs.get(ATTR_GROUP)
        return str(value) if value is not None else None

    @property
    def occupation(self) -> str | None:
        value = self.chunk.attrs.get(ATTR_OCCUPATION)
        return str(value) if value is not None else None


@dataclass(slots=True)
class RagAnswer:
    """The output of a full RAG turn."""

    query: str
    answer: str
    contexts: list[RetrievedChunk]
    cited_ranks: list[int] = field(default_factory=list)
    model: str = ""
    usage: dict[str, int] = field(default_factory=dict)

    @property
    def cited_contexts(self) -> list[RetrievedChunk]:
        """The retrieved chunks the answer actually cited.

        Citation-grounded scoring is what lets the harness measure generation
        bias without a sentiment classifier: the valence of what the model chose
        to cite is compared against the valence of everything it was given.
        """
        by_rank = {c.rank: c for c in self.contexts}
        return [by_rank[r] for r in self.cited_ranks if r in by_rank]
