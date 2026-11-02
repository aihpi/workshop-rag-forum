"""Chunk the downloaded Wikipedia articles and embed them with a local model.

Reads the parquet shards from data/dewiki/, splits each article into ~512-token
chunks (approximated by a word count), and embeds the chunks through an
OpenAI-compatible endpoint (minilm-embedding by default, configured in .env).

Vectors are stored as float32 .npy shards under data/embeddings/. The step is
resumable: a shard whose .npy already exists is skipped. Set MAX_CHUNKS to cap the
total number of chunks embedded (useful for a quick dry run).
"""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd
from dotenv import load_dotenv
from openai import OpenAI
from tqdm import tqdm

REPO_ROOT = Path(__file__).resolve().parents[2]
IN_DIR = REPO_ROOT / "data" / "dewiki"
OUT_DIR = REPO_ROOT / "data" / "embeddings"

load_dotenv(REPO_ROOT / ".env")

MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "minilm-embedding")
CHUNK_WORDS = int(os.environ.get("CHUNK_WORDS", 90))  # minilm caps input at 256 tokens
MAX_CHARS = int(os.environ.get("MAX_CHARS", 450))  # hard guard; embed_batch shrinks further on a 413
EMBED_BATCH = int(os.environ.get("EMBED_BATCH", 32))  # server caps batch at 32
MAX_CHUNKS = int(os.environ["MAX_CHUNKS"]) if os.environ.get("MAX_CHUNKS") else None


def client() -> OpenAI:
    return OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY", "not-needed"),
        base_url=os.environ.get("OPENAI_API_BASE"),
    )


def chunk_text(text: str, n_words: int) -> list[str]:
    words = text.split()
    chunks = [" ".join(words[i:i + n_words]) for i in range(0, len(words), n_words)
              if words[i:i + n_words]]
    return [c[:MAX_CHARS] for c in chunks]  # truncate to stay under the model's token cap


def embed_batch(cli: OpenAI, texts: list[str]) -> np.ndarray:
    # The token cap is per-input; a char cap is only a heuristic, so on a 413
    # ("must have less than N tokens") shrink every input and retry. Self-healing
    # so one dense chunk can't abort a long run.
    cap = MAX_CHARS
    for _ in range(8):
        try:
            resp = cli.embeddings.create(model=MODEL, input=[t[:cap] for t in texts])
            return np.array([d.embedding for d in resp.data], dtype=np.float32)
        except Exception as e:  # noqa: BLE001 - retry only on the token-limit 413
            if "256 tokens" not in str(e) and " tokens" not in str(e):
                raise
            cap = int(cap * 0.8)
    raise RuntimeError(f"could not fit batch under token cap (final char cap {cap})")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    cli = client()
    shards = sorted(IN_DIR.rglob("*.parquet"))
    if not shards:
        raise SystemExit(f"No parquet shards in {IN_DIR}; run 01_download_data.py first")

    total = 0
    for shard in shards:
        out_path = OUT_DIR / f"{shard.stem}.npy"
        if out_path.exists():
            n = len(np.load(out_path, mmap_mode="r"))
            total += n
            print(f"skip {shard.name} (already embedded, {n} vectors)")
            continue

        df = pd.read_parquet(shard, columns=["text"])
        chunks: list[str] = []
        for text in df["text"]:
            chunks.extend(chunk_text(text, CHUNK_WORDS))
            if MAX_CHUNKS is not None and total + len(chunks) >= MAX_CHUNKS:
                chunks = chunks[: MAX_CHUNKS - total]
                break

        vecs: list[np.ndarray] = []
        for i in tqdm(range(0, len(chunks), EMBED_BATCH), desc=shard.name):
            vecs.append(embed_batch(cli, chunks[i:i + EMBED_BATCH]))
        if not vecs:
            continue
        arr = np.vstack(vecs).astype(np.float32)
        np.save(out_path, arr)
        total += len(arr)
        print(f"saved {out_path.name}: {arr.shape} (total {total})")

        if MAX_CHUNKS is not None and total >= MAX_CHUNKS:
            break

    print(f"Done. {total} vectors in {OUT_DIR}")


if __name__ == "__main__":
    main()
