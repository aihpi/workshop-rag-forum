"""Compress the embeddings with turbovec and measure size + recall.

Loads the float32 vectors produced by 02_chunk_and_embed.py, then for each bit-width
builds a turbovec TurboQuantIndex, writes it to disk (to measure the compressed size),
and evaluates recall@k against an exact float32 brute-force search.

Vectors are L2-normalised so that inner product == cosine similarity, the standard
setup for embedding retrieval.

Writes data/results.json with, per bit-width: on-disk size, compression ratio vs the
float32 baseline, and recall@k.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import numpy as np
from turbovec import TurboQuantIndex

REPO_ROOT = Path(__file__).resolve().parents[2]
EMB_DIR = REPO_ROOT / "data" / "embeddings"
IDX_DIR = REPO_ROOT / "data" / "index"
RESULTS = REPO_ROOT / "data" / "results.json"

N_QUERIES = int(os.environ.get("N_QUERIES", 1000))
TOP_K = int(os.environ.get("TOP_K", 10))
# turbovec supports bit_width 2, 3, or 4 (vs float32's 32 bits/dim).
BIT_WIDTHS = [int(b) for b in os.environ.get("BIT_WIDTHS", "2,3,4").split(",")]


def load_vectors() -> np.ndarray:
    shards = sorted(EMB_DIR.glob("*.npy"))
    if not shards:
        raise SystemExit(f"No .npy embeddings in {EMB_DIR}; run 02_chunk_and_embed.py first")
    arr = np.vstack([np.load(s) for s in shards]).astype(np.float32)
    # L2-normalise -> inner product equals cosine similarity.
    arr /= np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    return np.ascontiguousarray(arr, dtype=np.float32)


def exact_topk(db: np.ndarray, queries: np.ndarray, k: int) -> np.ndarray:
    # Brute-force cosine top-k. db/queries are unit-normalised.
    sims = queries @ db.T
    return np.argpartition(-sims, kth=k, axis=1)[:, :k]


def main() -> None:
    IDX_DIR.mkdir(parents=True, exist_ok=True)
    vecs = load_vectors()
    n, dim = vecs.shape
    print(f"Loaded {n} vectors of dim {dim}")

    n_queries = min(N_QUERIES, n)
    # Use the first n_queries vectors as queries against the whole corpus.
    queries = np.ascontiguousarray(vecs[:n_queries], dtype=np.float32)
    truth = exact_topk(vecs, queries, TOP_K)

    float32_bytes = n * dim * 4
    results = {
        "n_vectors": n,
        "dim": dim,
        "top_k": TOP_K,
        "n_queries": n_queries,
        "baseline_float32": {
            "bits_per_dim": 32,
            "bytes": float32_bytes,
            "compression_ratio": 1.0,
        },
        "turbovec": {},
    }

    for b in BIT_WIDTHS:
        index = TurboQuantIndex(dim=dim, bit_width=b)
        index.add(vecs)
        idx_path = IDX_DIR / f"index_{b}bit.tv"
        index.write(str(idx_path))
        size = idx_path.stat().st_size

        index.prepare()  # warm caches so timing/quality is the steady-state behaviour
        _, ids = index.search(queries, k=TOP_K)  # ids shape: (n_queries, TOP_K)
        ids = np.asarray(ids)
        hits = sum(len(set(ids[qi].tolist()) & set(truth[qi].tolist()))
                   for qi in range(n_queries))
        recall = hits / (n_queries * TOP_K)

        results["turbovec"][f"{b}bit"] = {
            "bits_per_dim": b,
            "bytes": size,
            "compression_ratio": float32_bytes / size if size else None,
            f"recall@{TOP_K}": recall,
        }
        print(f"{b}-bit: {size / 1e6:.2f} MB  "
              f"({float32_bytes / size:.1f}x)  recall@{TOP_K}={recall:.3f}")

    RESULTS.write_text(json.dumps(results, indent=2))
    print(f"Wrote {RESULTS}")


if __name__ == "__main__":
    main()
