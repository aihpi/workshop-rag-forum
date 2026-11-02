"""The RAG pipeline: retrieve, then generate."""

from __future__ import annotations

from dataclasses import dataclass

from .generation import Generator
from .retrieval import Retriever
from .types import RagAnswer, RetrievedChunk


@dataclass(slots=True)
class RagPipeline:
    """Ties a retriever to a generator.

    `generator` is optional so the retrieval-only bias experiments (and any
    embeddings-only deployment) work without a chat model configured.
    """

    retriever: Retriever
    generator: Generator | None = None
    top_k: int = 5

    @property
    def name(self) -> str:
        gen = self.generator.name if self.generator else "none"
        return f"{self.retriever.name}+{gen}@k={self.top_k}"

    def retrieve(self, query: str, k: int | None = None) -> list[RetrievedChunk]:
        return self.retriever.retrieve(query, k=k or self.top_k)

    def answer(
        self,
        query: str,
        k: int | None = None,
        contexts: list[RetrievedChunk] | None = None,
    ) -> RagAnswer:
        """Answer `query`.

        Passing `contexts` skips retrieval and generates from exactly those
        passages. The bias harness relies on this to hold context fixed while
        varying only the query, which separates generator bias from retriever
        bias.
        """
        if self.generator is None:
            raise RuntimeError(
                "no generator configured; set OPENAI_CHAT_MODEL and pass an "
                "OpenAIGenerator, or use .retrieve() for retrieval-only runs"
            )
        used = self.retrieve(query, k=k) if contexts is None else contexts
        return self.generator.generate(query, used)
