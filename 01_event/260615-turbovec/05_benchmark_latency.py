"""Benchmark query latency: float32 brute-force vs turbovec at 2/3/4-bit.

Loads the embeddings produced by 02_chunk_and_embed.py, rebuilds a TurboQuantIndex
per bit-width (same as 03), and times a batch of queries against:
  - an exact float32 brute-force cosine search (the baseline), and
  - turbovec's compressed search at each bit-width.

Each search is repeated REPEATS times; the median wall-time is reported as mean
latency per query (ms) and throughput (queries/s). Latency fields are merged into
data/results.json so 06_make_latency_figure / the slides can read real numbers.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

import numpy as np
from turbovec import TurboQuantIndex

REPO_ROOT = Path(__file__).resolve().parents[2]
EMB_DIR = REPO_ROOT / "data" / "embeddings"
RESULTS = REPO_ROOT / "data" / "results.json"

N_QUERIES = int(os.environ.get("N_QUERIES", 1000))
TOP_K = int(os.environ.get("TOP_K", 10))
REPEATS = int(os.environ.get("REPEATS", 5))
BIT_WIDTHS = [int(b) for b in os.environ.get("BIT_WIDTHS", "2,3,4").split(",")]


def load_vectors() -> np.ndarray:
    shards = sorted(EMB_DIR.glob("*.npy"))
    if not shards:
        raise SystemExit(f"No .npy embeddings in {EMB_DIR}; run 02_chunk_and_embed.py first")
    arr = np.vstack([np.load(s) for s in shards]).astype(np.float32)
    arr /= np.linalg.norm(arr, axis=1, keepdims=True) + 1e-12
    return np.ascontiguousarray(arr, dtype=np.float32)


def time_call(fn, repeats: int) -> float:
    fn()  # warm-up (caches, BLAS threads, page-ins)
    times = []
    for _ in range(repeats):
        t0 = time.perf_counter()
        fn()
        times.append(time.perf_counter() - t0)
    return float(np.median(times))


def main() -> None:
    vecs = load_vectors()
    n, dim = vecs.shape
    queries = np.ascontiguousarray(vecs[:min(N_QUERIES, n)], dtype=np.float32)
    nq = len(queries)
    print(f"Loaded {n} vectors of dim {dim}; benchmarking {nq} queries, k={TOP_K}, "
          f"median of {REPEATS} repeats")

    def float32_search():
        sims = queries @ vecs.T
        return np.argpartition(-sims, kth=TOP_K, axis=1)[:, :TOP_K]

    baseline_s = time_call(float32_search, REPEATS)
    rows = {"float32": baseline_s}
    print(f"float32 brute-force: {baseline_s / nq * 1e3:.3f} ms/query  "
          f"({nq / baseline_s:,.0f} q/s)")

    per_bit = {}
    for b in BIT_WIDTHS:
        index = TurboQuantIndex(dim=dim, bit_width=b)
        index.add(vecs)
        index.prepare()
        secs = time_call(lambda: index.search(queries, k=TOP_K), REPEATS)
        rows[f"{b}bit"] = secs
        per_bit[b] = secs
        print(f"{b}-bit turbovec:     {secs / nq * 1e3:.3f} ms/query  "
              f"({nq / secs:,.0f} q/s)  speedup {baseline_s / secs:.2f}x")

    # Merge latency into results.json without clobbering size/recall.
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {"turbovec": {}}
    results.setdefault("latency", {})
    results["latency"] = {
        "n_queries": nq,
        "top_k": TOP_K,
        "repeats": REPEATS,
        "float32_ms_per_query": baseline_s / nq * 1e3,
        "float32_qps": nq / baseline_s,
    }
    for b, secs in per_bit.items():
        results["turbovec"].setdefault(f"{b}bit", {})
        results["turbovec"][f"{b}bit"]["latency_ms_per_query"] = secs / nq * 1e3
        results["turbovec"][f"{b}bit"]["qps"] = nq / secs
        results["turbovec"][f"{b}bit"]["speedup_vs_float32"] = baseline_s / secs
    RESULTS.write_text(json.dumps(results, indent=2))
    print(f"Merged latency into {RESULTS}")


if __name__ == "__main__":
    main()
