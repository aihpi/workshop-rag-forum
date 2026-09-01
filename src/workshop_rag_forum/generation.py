"""Answer generation over retrieved context.

Context is presented as a numbered list and the model is required to cite the
passages it used as `[n]`. Those citations are not decoration: parsing them tells
the harness *which* of the offered passages the model actually grounded in, which
is how generation bias is measured without a sentiment classifier in the loop.
"""

from __future__ import annotations

import re
import time
from typing import Protocol, runtime_checkable

from openai import OpenAI

from .config import Settings, get_settings
from .types import RagAnswer, RetrievedChunk

SYSTEM_PROMPT = (
    "You answer questions using only the numbered context passages provided. "
    "Cite every passage you rely on as [n], matching its number. "
    "If the context does not contain the answer, say so plainly instead of "
    "guessing. Be concise."
)

CITATION_RE = re.compile(r"\[(\d+)\]")


@runtime_checkable
class Generator(Protocol):
    @property
    def name(self) -> str: ...

    def generate(self, query: str, contexts: list[RetrievedChunk]) -> RagAnswer: ...


def format_context(contexts: list[RetrievedChunk]) -> str:
    """Render contexts as a numbered list. Numbers are 1-based for the model."""
    return "\n\n".join(
        f"[{c.rank + 1}] ({c.chunk.source}) {c.chunk.text}" for c in contexts
    )


def build_prompt(query: str, contexts: list[RetrievedChunk]) -> str:
    return f"Context passages:\n\n{format_context(contexts)}\n\nQuestion: {query}"


def parse_citations(answer: str, n_contexts: int) -> list[int]:
    """Extract 0-based context ranks cited in `answer`, in order of appearance.

    Out-of-range numbers are dropped: a model citing [9] when it was given five
    passages has hallucinated the reference, and counting it would corrupt the
    grounding metrics.
    """
    seen: list[int] = []
    for match in CITATION_RE.finditer(answer):
        rank = int(match.group(1)) - 1
        if 0 <= rank < n_contexts and rank not in seen:
            seen.append(rank)
    return seen


class OpenAIGenerator:
    """Chat completion via any OpenAI-compatible endpoint (e.g. a LiteLLM proxy)."""

    def __init__(self, settings: Settings | None = None, client: OpenAI | None = None):
        self.settings: Settings = settings or get_settings()
        self.model: str = self.settings.require_chat_model()
        self._client: OpenAI = client or OpenAI(
            api_key=self.settings.api_key,
            base_url=self.settings.api_base,
            timeout=self.settings.request_timeout,
        )

    @property
    def name(self) -> str:
        return self.model

    def generate(self, query: str, contexts: list[RetrievedChunk]) -> RagAnswer:
        last_error: Exception | None = None
        for attempt in range(self.settings.max_retries):
            try:
                response = self._client.chat.completions.create(
                    model=self.model,
                    temperature=self.settings.temperature,
                    max_tokens=self.settings.max_tokens,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": build_prompt(query, contexts)},
                    ],
                )
                text = (response.choices[0].message.content or "").strip()
                usage = response.usage
                return RagAnswer(
                    query=query,
                    answer=text,
                    contexts=contexts,
                    cited_ranks=parse_citations(text, len(contexts)),
                    model=self.model,
                    usage={
                        "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
                        "completion_tokens": getattr(usage, "completion_tokens", 0)
                        or 0,
                    },
                )
            except Exception as error:  # noqa: BLE001 - retried, then re-raised
                last_error = error
                if attempt == self.settings.max_retries - 1:
                    raise
                time.sleep(2**attempt * 0.5)
        raise RuntimeError("unreachable") from last_error


class EchoGenerator:
    """Offline generator that cites the top `n_cite` passages verbatim.

    Deliberately unbiased: it lets the harness and its tests be exercised without
    a network, and any bias the metrics then report is a bug in the metrics.
    """

    def __init__(self, n_cite: int = 3):
        self.n_cite: int = n_cite

    @property
    def name(self) -> str:
        return f"echo-{self.n_cite}"

    def generate(self, query: str, contexts: list[RetrievedChunk]) -> RagAnswer:
        chosen = contexts[: self.n_cite]
        citations = " ".join(f"[{c.rank + 1}]" for c in chosen)
        summary = " ".join(" ".join(c.chunk.text.split()[:20]) for c in chosen)
        text = f"{summary} {citations}".strip()
        return RagAnswer(
            query=query,
            answer=text,
            contexts=contexts,
            cited_ranks=[c.rank for c in chosen],
            model=self.name,
        )
