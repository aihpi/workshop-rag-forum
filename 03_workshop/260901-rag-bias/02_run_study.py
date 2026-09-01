"""Run the bias study on both corpus variants.

    uv run python 03_workshop/260901-rag-bias/02_run_study.py

Environment: KS (default "10,100"), RETRIEVER (default "dense"), OFFLINE=1.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / "src"))

from workshop_rag_forum.cli import main  # noqa: E402

KS = os.environ.get("KS", "10,100")
RETRIEVER = os.environ.get("RETRIEVER", "dense")
OFFLINE = ["--offline"] if os.environ.get("OFFLINE") else []

for variant in ("R", "K"):
    print(f"\n{'=' * 60}\nVariante {variant}\n{'=' * 60}")
    code = main([*OFFLINE, "study", "--variant", variant,
                 "--ks", KS, "--retriever", RETRIEVER])
    if code != 0:
        raise SystemExit(code)
