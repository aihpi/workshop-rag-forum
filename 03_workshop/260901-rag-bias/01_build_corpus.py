"""Build both corpus variants (R and K) end to end.

Wikidata populations and Wikipedia extracts are cached under data/corpus/, so
the second variant costs only the articles the first one did not already fetch.

    uv run python 03_workshop/260901-rag-bias/01_build_corpus.py

Environment: PER_OCCUPATION (default 400), OFFLINE=1 for hash embeddings.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from workshop_rag_forum.cli import main  # noqa: E402

PER_OCCUPATION = os.environ.get("PER_OCCUPATION", "400")
OFFLINE = ["--offline"] if os.environ.get("OFFLINE") else []

for variant in ("R", "K"):
    print(f"\n{'=' * 60}\nVariante {variant}\n{'=' * 60}")
    code = main([*OFFLINE, "build-corpus", "--variant", variant,
                 "--per-occupation", PER_OCCUPATION])
    if code != 0:
        raise SystemExit(code)
