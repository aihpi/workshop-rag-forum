"""Command line interface: build the corpus, query it, run the bias study."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from .bias import print_summary, run_study, write_results
from .biographies import (
    DEFAULT_OCCUPATIONS,
    GROUPS,
    VARIANT_BALANCED,
    VARIANT_REALISTIC,
    build_documents,
    fetch_extracts,
    load_or_fetch_populations,
    sample_population,
)
from .chunking import chunk_documents
from .config import ConfigError, Settings, get_settings
from .embedding import Embedder, HashEmbedder, OpenAIEmbedder
from .generation import EchoGenerator, Generator, OpenAIGenerator
from .pipeline import RagPipeline
from .retrieval import DenseRetriever, MMRRetriever, Retriever, TurboVecRetriever
from .store import VectorStore
from .types import Document


def _embedder(settings: Settings, offline: bool) -> Embedder:
    return HashEmbedder() if offline else OpenAIEmbedder(settings)


def _generator(settings: Settings, offline: bool) -> Generator | None:
    if offline:
        return EchoGenerator()
    try:
        return OpenAIGenerator(settings)
    except ConfigError as error:
        print(f"warning: {error}\n  continuing without generation.", file=sys.stderr)
        return None


def _retriever(
    name: str, store: VectorStore, embedder: Embedder, mmr_lambda: float = 0.5
) -> Retriever:
    if name == "dense":
        return DenseRetriever(store, embedder)
    if name == "mmr":
        return MMRRetriever(store, embedder, lambda_=mmr_lambda)
    if name.startswith("turbovec"):
        bits = int(name.removeprefix("turbovec").lstrip("-") or 4)
        return TurboVecRetriever(store, embedder, bit_width=bits)
    raise SystemExit(f"unknown retriever {name!r}")


def _store_dir(settings: Settings, variant: str, override: str | None) -> Path:
    return Path(override) if override else settings.index_dir / f"variant_{variant}"


# ---- commands -------------------------------------------------------------


def cmd_build_corpus(args: argparse.Namespace) -> int:
    """Fetch populations from Wikidata, sample a variant, embed it."""
    settings = get_settings()
    populations = load_or_fetch_populations(
        DEFAULT_OCCUPATIONS, settings.corpus_dir, quiet=False
    )

    people: list[dict[str, str]] = []
    for occupation in DEFAULT_OCCUPATIONS:
        sampled = sample_population(
            populations[occupation.label],
            n=args.per_occupation,
            variant=args.variant,
            seed=args.seed,
        )
        people.extend(sampled)
        print(
            f"  sampled {len(sampled):5d} for {occupation.label} (variant {args.variant})"
        )

    cache = settings.corpus_dir / "extracts.json"
    extracts: dict[str, str] = json.loads(cache.read_text()) if cache.exists() else {}
    missing = sorted({p["title"] for p in people} - set(extracts))
    if missing:
        print(f"fetching {len(missing)} article extracts from de.wikipedia.org ...")
        extracts = fetch_extracts(missing, cache_path=cache, existing=extracts)

    documents: list[Document] = build_documents(people, extracts, variant=args.variant)
    print(
        f"{len(documents)} documents with usable text "
        f"({len(people) - len(documents)} dropped as too short)"
    )

    # Dropping short articles is a selection on article length. If that selection
    # is not gender-neutral it shifts p0 away from the Wikidata population, so
    # report it rather than let it pass silently.
    kept = {d.attrs["qid"] for d in documents}
    for group in GROUPS:
        total = sum(1 for p in people if p["gender"] == group)
        if not total:
            continue
        survived = sum(1 for p in people if p["gender"] == group and p["qid"] in kept)
        print(f"  kept {survived:5d}/{total:5d} {group:8s} ({survived / total:.1%})")

    chunks = chunk_documents(
        documents,
        n_words=settings.chunk_words,
        overlap_words=settings.chunk_overlap_words,
        max_chars=settings.max_chars,
    )
    embedder = _embedder(settings, args.offline)
    print(f"embedding {len(chunks)} chunks with {embedder.name} ...")

    store = VectorStore.build(chunks, embedder)
    out = _store_dir(settings, args.variant, args.out)
    store.save(out)
    print(f"wrote store to {out} ({len(store)} chunks, dim {store.dim})")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    settings = get_settings()
    store = VectorStore.load(_store_dir(settings, args.variant, args.store))
    embedder = _embedder(settings, args.offline)
    pipeline = RagPipeline(
        retriever=_retriever(args.retriever, store, embedder, args.mmr_lambda),
        generator=None if args.no_generate else _generator(settings, args.offline),
        top_k=args.k,
    )

    contexts = pipeline.retrieve(args.question)
    print(f"\nTop {len(contexts)} via {pipeline.retriever.name}:\n")
    for item in contexts:
        label = f" [{item.group}]" if item.group else ""
        print(f"  {item.rank + 1:3d}. {item.score:+.3f}{label} {item.chunk.title}")

    if pipeline.generator is not None:
        answer = pipeline.answer(args.question, contexts=contexts)
        print(f"\nAnswer ({answer.model}):\n{answer.answer}")
    return 0


def cmd_study(args: argparse.Namespace) -> int:
    settings = get_settings()
    store = VectorStore.load(_store_dir(settings, args.variant, args.store))
    embedder = _embedder(settings, args.offline)
    results = run_study(
        store,
        _retriever(args.retriever, store, embedder, args.mmr_lambda),
        DEFAULT_OCCUPATIONS,
        ks=[int(k) for k in args.ks.split(",")],
        variant=args.variant,
        seed=args.seed,
    )
    out = (
        Path(args.out)
        if args.out
        else settings.results_dir / f"study_{args.variant}.json"
    )
    write_results(results, out)
    print_summary(results, headline_k=int(args.ks.split(",")[0]))
    print(f"\nWrote {out}")
    return 0


def cmd_show(args: argparse.Namespace) -> int:
    settings = get_settings()
    path = (
        Path(args.results)
        if args.results
        else (settings.results_dir / f"study_{args.variant}.json")
    )
    results: dict[str, Any] = json.loads(path.read_text())
    print_summary(results, headline_k=args.k)
    return 0


# ---- entry point ----------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="workshop-rag",
        description="RAG pipeline and retrieval bias study (A = p_k/p0).",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="hash embeddings + stub generator; no embedding endpoint",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    build = sub.add_parser("build-corpus", help="fetch, sample and embed the corpus")
    build.add_argument(
        "--variant",
        choices=[VARIANT_REALISTIC, VARIANT_BALANCED],
        default=VARIANT_REALISTIC,
    )
    build.add_argument("--per-occupation", type=int, default=400)
    build.add_argument("--seed", type=int, default=0)
    build.add_argument("--out")
    build.set_defaults(func=cmd_build_corpus)

    query = sub.add_parser("query", help="run one query through the pipeline")
    query.add_argument("question")
    query.add_argument("--variant", default=VARIANT_REALISTIC)
    query.add_argument("--store")
    query.add_argument("-k", type=int, default=10)
    query.add_argument(
        "--retriever", default="dense", help="dense | mmr | turbovec-{2,3,4}"
    )
    query.add_argument("--mmr-lambda", type=float, default=0.5)
    query.add_argument("--no-generate", action="store_true")
    query.set_defaults(func=cmd_query)

    study = sub.add_parser("study", help="run the bias study on a corpus variant")
    study.add_argument(
        "--variant",
        choices=[VARIANT_REALISTIC, VARIANT_BALANCED],
        default=VARIANT_REALISTIC,
    )
    study.add_argument("--store")
    study.add_argument(
        "--ks", default="10,100", help="k values; the first is the headline"
    )
    study.add_argument("--seed", type=int, default=0)
    study.add_argument("--retriever", default="dense")
    study.add_argument("--mmr-lambda", type=float, default=0.5)
    study.add_argument("--out")
    study.set_defaults(func=cmd_study)

    show = sub.add_parser("show", help="print a summary of saved results")
    show.add_argument("--results")
    show.add_argument("--variant", default=VARIANT_REALISTIC)
    show.add_argument("-k", type=int, default=10)
    show.set_defaults(func=cmd_show)

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
