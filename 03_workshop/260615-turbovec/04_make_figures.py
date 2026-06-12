"""Render comparison figures from data/results.json.

Produces, into this meeting folder:
  fig_storage_size.png     absolute store size (float32 baseline vs 2/4/8-bit)
  fig_compression_ratio.png compression factor vs float32
  fig_recall.png           recall@k vs bit-width
  fig_tradeoff.png         storage-vs-recall trade-off
"""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent
RESULTS = REPO_ROOT / "data" / "results.json"


def main() -> None:
    if not RESULTS.exists():
        raise SystemExit(f"{RESULTS} not found; run 03_compress_turbovec.py first")
    r = json.loads(RESULTS.read_text())
    k = r["top_k"]

    tv = r["turbovec"]
    widths = sorted(tv, key=lambda key: tv[key]["bits_per_dim"])  # e.g. ["2bit","4bit","8bit"]
    labels = [w.replace("bit", "-bit") for w in widths]
    sizes_mb = [tv[w]["bytes"] / 1e6 for w in widths]
    ratios = [tv[w]["compression_ratio"] for w in widths]
    recalls = [tv[w][f"recall@{k}"] for w in widths]
    base_mb = r["baseline_float32"]["bytes"] / 1e6

    # 1) Storage size: baseline + each bit-width.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(["float32\n(baseline)"] + labels, [base_mb] + sizes_mb,
                  color=["#888"] + ["#2a7ab9"] * len(labels))
    ax.set_ylabel("Store size (MB)")
    ax.set_title(f"Storage for {r['n_vectors']:,} vectors (dim {r['dim']})")
    ax.bar_label(bars, fmt="%.1f")
    fig.tight_layout()
    fig.savefig(HERE / "fig_storage_size.png", dpi=150)

    # 2) Compression ratio.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, ratios, color="#2a7ab9")
    ax.set_ylabel("Compression factor vs float32")
    ax.set_title("turbovec compression ratio")
    ax.bar_label(bars, fmt="%.1fx")
    fig.tight_layout()
    fig.savefig(HERE / "fig_compression_ratio.png", dpi=150)

    # 3) Recall@k.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    bars = ax.bar(labels, recalls, color="#c0563b")
    ax.set_ylim(0, 1)
    ax.set_ylabel(f"recall@{k}")
    ax.set_title(f"Retrieval quality vs exact float32 search (recall@{k})")
    ax.bar_label(bars, fmt="%.3f")
    fig.tight_layout()
    fig.savefig(HERE / "fig_recall.png", dpi=150)

    # 4) Trade-off: size vs recall.
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.scatter(sizes_mb, recalls, color="#2a7ab9", zorder=3)
    for x, y, lab in zip(sizes_mb, recalls, labels):
        ax.annotate(lab, (x, y), textcoords="offset points", xytext=(6, 6))
    ax.set_xlabel("Store size (MB)")
    ax.set_ylabel(f"recall@{k}")
    ax.set_title("Storage vs retrieval-quality trade-off")
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(HERE / "fig_tradeoff.png", dpi=150)

    print(f"Wrote 4 figures to {HERE}")


if __name__ == "__main__":
    main()
