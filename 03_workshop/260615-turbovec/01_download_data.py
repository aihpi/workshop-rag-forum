"""Download a ~512 MB subset of German Wikipedia by whole parquet shards.

Source: the `wikimedia/wikipedia` dataset on the Hugging Face Hub, config
`20231101.de`. Each config is stored as a set of parquet shards of known size, so
downloading whole shards until a byte target is reached gives a *predictable* corpus
size (unlike streaming row-by-row).

Output: parquet shards under <repo>/data/dewiki/.
"""

from __future__ import annotations

import os
from pathlib import Path

from huggingface_hub import HfApi, hf_hub_download

REPO_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = REPO_ROOT / "data" / "dewiki"

DATASET = "wikimedia/wikipedia"
CONFIG_PREFIX = "20231101.de/"  # German dump, snapshot 2023-11-01
TARGET_BYTES = int(os.environ.get("TARGET_BYTES", 512_000_000))


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    api = HfApi()

    # List parquet shards for the German config, with their sizes.
    info = api.repo_info(DATASET, repo_type="dataset", files_metadata=True)
    shards = sorted(
        (s for s in info.siblings if s.rfilename.startswith(CONFIG_PREFIX)
         and s.rfilename.endswith(".parquet")),
        key=lambda s: s.rfilename,
    )
    if not shards:
        raise SystemExit(f"No parquet shards found under {CONFIG_PREFIX} in {DATASET}")

    print(f"Found {len(shards)} shards for {CONFIG_PREFIX}; "
          f"target ~{TARGET_BYTES / 1e6:.0f} MB")

    downloaded = 0
    for s in shards:
        if downloaded >= TARGET_BYTES:
            break
        size = s.size or 0
        print(f"  downloading {s.rfilename} (~{size / 1e6:.1f} MB) ...")
        hf_hub_download(
            DATASET,
            s.rfilename,
            repo_type="dataset",
            local_dir=OUT_DIR,
        )
        downloaded += size

    got = sum(p.stat().st_size for p in OUT_DIR.rglob("*.parquet"))
    print(f"Done. {got / 1e6:.1f} MB of parquet in {OUT_DIR}")


if __name__ == "__main__":
    main()
