"""Configuration, read once from the environment / .env.

Everything talks to a single OpenAI-compatible endpoint. Against a LiteLLM proxy
that means one base URL and one key for both embeddings and chat; the model names
are whatever your proxy exposes, so they have no provider-specific defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[2]


class ConfigError(RuntimeError):
    """A required setting is missing or unusable."""


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    return float(raw) if raw else default


@dataclass(slots=True)
class Settings:
    """Resolved runtime settings."""

    api_key: str = "not-needed"
    api_base: str | None = None
    embedding_model: str = "minilm-embedding"
    # No default: on a LiteLLM proxy the chat deployment name is site-specific,
    # and guessing one would silently call a model the operator does not host.
    chat_model: str = ""
    embedding_dim: int | None = None

    embed_batch: int = 32
    max_chars: int = 450
    chunk_words: int = 90
    chunk_overlap_words: int = 20

    temperature: float = 0.0
    max_tokens: int = 512
    request_timeout: float = 60.0
    max_retries: int = 5

    data_dir: Path = field(default_factory=lambda: REPO_ROOT / "data")

    @classmethod
    def from_env(cls, env_file: Path | None = None) -> Settings:
        load_dotenv(env_file or REPO_ROOT / ".env")
        data_dir = os.environ.get("RAG_DATA_DIR")
        return cls(
            api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
            api_base=os.environ.get("OPENAI_API_BASE"),
            embedding_model=os.environ.get(
                "OPENAI_EMBEDDING_MODEL", "minilm-embedding"
            ),
            chat_model=os.environ.get("OPENAI_CHAT_MODEL", ""),
            embedding_dim=_env_int("OPENAI_EMBEDDING_DIM", 0) or None,
            embed_batch=_env_int("EMBED_BATCH", 32),
            max_chars=_env_int("MAX_CHARS", 450),
            chunk_words=_env_int("CHUNK_WORDS", 90),
            chunk_overlap_words=_env_int("CHUNK_OVERLAP_WORDS", 20),
            temperature=_env_float("RAG_TEMPERATURE", 0.0),
            max_tokens=_env_int("RAG_MAX_TOKENS", 512),
            request_timeout=_env_float("RAG_TIMEOUT", 60.0),
            max_retries=_env_int("RAG_MAX_RETRIES", 5),
            data_dir=Path(data_dir) if data_dir else REPO_ROOT / "data",
        )

    def require_chat_model(self) -> str:
        if not self.chat_model:
            raise ConfigError(
                "No chat model configured. Set OPENAI_CHAT_MODEL in .env to a "
                "deployment name your endpoint serves (see .env_example)."
            )
        return self.chat_model

    @property
    def index_dir(self) -> Path:
        return self.data_dir / "index"

    @property
    def corpus_dir(self) -> Path:
        return self.data_dir / "corpus"

    @property
    def results_dir(self) -> Path:
        return self.data_dir / "results"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings.from_env()
