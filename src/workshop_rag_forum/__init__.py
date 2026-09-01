"""A RAG pipeline and a harness for measuring bias in it.

Typical use:

    from workshop_rag_forum import (
        DenseRetriever, OpenAIEmbedder, RagPipeline, VectorStore, get_settings,
    )

    settings = get_settings()
    store = VectorStore.load(settings.index_dir)
    embedder = OpenAIEmbedder(settings)
    pipeline = RagPipeline(DenseRetriever(store, embedder), top_k=5)
    print(pipeline.retrieve("Who led the migration?"))

The bias harness lives in `workshop_rag_forum.bias`. The CLI is
`workshop_rag_forum.cli`, deliberately not re-exported here: it imports from this
package, so pulling it back in would make the import graph cyclic.
"""

from .biographies import (
    DEFAULT_OCCUPATIONS,
    GROUPS,
    Occupation,
    base_rates,
    build_documents,
    fetch_population,
    sample_population,
)
from .chunking import chunk_document, chunk_documents, split_words
from .config import ConfigError, Settings, get_settings
from .embedding import Embedder, HashEmbedder, OpenAIEmbedder, l2_normalise
from .generation import EchoGenerator, Generator, OpenAIGenerator, parse_citations
from .pipeline import RagPipeline
from .retrieval import DenseRetriever, MMRRetriever, Retriever, TurboVecRetriever
from .store import VectorStore
from .types import Chunk, Document, RagAnswer, RetrievedChunk

__all__ = [
    "Chunk",
    "ConfigError",
    "DenseRetriever",
    "Document",
    "EchoGenerator",
    "Embedder",
    "Generator",
    "HashEmbedder",
    "MMRRetriever",
    "OpenAIEmbedder",
    "OpenAIGenerator",
    "RagAnswer",
    "RagPipeline",
    "RetrievedChunk",
    "Retriever",
    "Settings",
    "TurboVecRetriever",
    "VectorStore",
    "chunk_document",
    "chunk_documents",
    "DEFAULT_OCCUPATIONS",
    "GROUPS",
    "Occupation",
    "base_rates",
    "build_documents",
    "get_settings",
    "l2_normalise",
    "fetch_population",
    "sample_population",
    "parse_citations",
    "split_words",
]
