# Architecture

How this repository is organised and why: the parts that outlive any single
meeting. For the 260901 session's method see
[03_workshop/260901-rag-bias/METHOD.md](03_workshop/260901-rag-bias/METHOD.md).
For setup see [installation.md](installation.md); for developer workflows see
[development.md](development.md).

## What the repository is

Two things that are deliberately kept apart:

1. **A reusable RAG pipeline** in `src/workshop_rag_forum/`. Stable across
   meetings. Every stage is swappable, which is the whole point: a meeting's
   question is usually "what changes if I swap *this* stage?"
2. **One folder per meeting** in `03_workshop/YYMMDD-topic/`. Meeting folders are
   thin drivers plus documentation plus figures. They may be messy and dated; the
   package may not.

The rule of thumb: if a second meeting could use it, it belongs in the package.
The same rule applies to documentation. This file holds what is durable;
meeting folders hold what is specific to one question.

## Top-level layout

```
├── src/workshop_rag_forum/   the pipeline and the bias study (the only importable code)
├── tests/                    pytest suite for the package; no network
├── 03_workshop/              one folder per meeting
│   ├── 260615-turbovec/        vector compression vs. a float32 baseline
│   └── 260901-rag-bias/        retrieval bias (see its METHOD.md and README.md)
├── 00_aisc/img/              AISC and funder logos used in the READMEs
├── devtools/lint.py          codespell + ruff + basedpyright, invoked by `make lint`
├── data/                     generated corpora, indexes, results (gitignored)
├── docs/                     (empty) long-form documentation
├── notebooks/                (empty) exploratory notebooks
├── references/               (empty) papers, specs, external material
├── reports/                  (empty) generated reports
├── .github/workflows/        ci.yml (lint + test) and buld_publish.yml
│
├── ARCHITECTURE.md           this file
├── README.md                 project overview, meeting index, quick start
├── installation.md           installing uv and Python
├── development.md            developer workflows and IDE setup
├── publishing.md             release/publishing notes (from the template)
├── Makefile                  install · lint · test · build · clean · upgrade
├── pyproject.toml            dependencies, entry points, ruff/basedpyright/pytest config
├── uv.lock                   resolved dependency lockfile
├── .env_example              copy to .env; endpoint URL, key, model names
├── .gitignore                excludes data/, .env, build artefacts
├── .copier-answers.yml       provenance from the aihpi/template-ai-project template
└── LICENSE                   MIT
```

The four empty directories carry a `.gitkeep` and come from the project
template. They are kept so generated output has a conventional home.

## The package

| Module | What it does |
|---|---|
| `types.py` | The four dataclasses that cross module boundaries (`Document`, `Chunk`, `RetrievedChunk`, `RagAnswer`) plus the `attrs` key names. Everything else depends on this and it depends on nothing. |
| `config.py` | Reads `.env` once into a `Settings` object: endpoint URL, API key, model names, chunking parameters, and the `data/` path layout. Fails loudly on a missing chat model rather than guessing one. |
| `chunking.py` | Splits a document into overlapping word windows. Never truncates: an over-long window is split again on a word boundary, so no source text is silently lost. |
| `embedding.py` | Turns text into unit-normalised vectors. `OpenAIEmbedder` talks to any OpenAI-compatible endpoint and shrinks-and-retries when the endpoint rejects an input as too long; `HashEmbedder` is a deterministic offline stand-in. |
| `store.py` | `VectorStore` holds chunks and their vectors **row-aligned**, does exact cosine top-k, and persists to parquet + `.npy`. Validates the alignment on construction. |
| `retrieval.py` | Query text in, ranked `RetrievedChunk`s out. `DenseRetriever` (plain cosine), `MMRRetriever` (diversity reranking), `DetGreedyRetriever` (fairness-aware reranking: a minimum share per group in every prefix), `TurboVecRetriever` (quantised search reusing the 260615 index). |
| `generation.py` | Builds a numbered-context prompt, calls the chat model, and parses the `[n]` citations back out, so it is recorded which passages the answer actually used. |
| `pipeline.py` | `RagPipeline`: a retriever plus an optional generator. Generation is optional so retrieval-only studies need no chat model. |
| `biographies.py` | Builds the 260901 study corpus. The one module tied to a specific meeting; documented in that meeting's METHOD.md. |
| `cli.py` | The `workshop-rag` command: `build-corpus`, `query`, `study`, `show`. |
| `bias/ratio.py` | The headline metric A = p_k/p0, its bootstrap intervals and its refusal rules. |
| `bias/quality.py` | nDCG@k against binary occupation relevance, so a fairness intervention can be priced in the ranking quality it costs. |
| `bias/covariate.py` | Article length as a covariate, controlled by recomputing A inside length terciles rather than by fitting a model. |
| `bias/study.py` | Runs all of it across strata and *k* values (amplification, nDCG, the terciles, and a DetGreedy sweep from no correction to full parity) and writes a self-describing results file. |

## The pipeline

The generic path, independent of any corpus:

```
Document          raw text plus a dict of ground-truth labels
    │
    ▼  chunk_documents          overlapping windows; labels copied onto each
Chunk[]
    │
    ▼  Embedder.embed           unit-normalised vectors
VectorStore                     chunks and vectors, row-aligned, persisted together
    │
    ▼  Retriever.retrieve       query text → ranked hits with scores
RetrievedChunk[]
    │
    ▼  Generator.generate       numbered-context prompt → answer + parsed citations
RagAnswer
```

Anything downstream (a metric, a figure, an application) reads these four
types and nothing else.

## The `attrs` contract

This is the main extension point, and the reason a study can measure ground truth
without a sentiment classifier or an LLM judge in the loop.

**The idea.** Every document carries a small dictionary of labels alongside its
text. Those labels are copied onto each chunk cut from it, survive being written
to disk, and come back attached to every search result. So when a retriever
returns a passage, the code already knows what that passage is, as fact rather
than as a guess.

```python
Document(
    doc_id="Q40871",
    text="Hannelore Elsner war eine deutsche Schauspielerin ...",
    attrs={"gender": "female", "occupations": ["Schauspiel"], "qid": "Q40871"},
)
```

**How it travels.**

1. `chunk_document` copies `attrs` onto every `Chunk`. A *copy*, so editing one
   chunk's labels cannot corrupt its siblings.
2. `VectorStore.save` serialises it to a JSON column in `chunks.parquet`, which
   round-trips types intact: an integer comes back an integer, a list a list.
3. `RetrievedChunk` exposes the common keys as properties, so a metric reads
   `hit.group` rather than digging through a dictionary.

**Absent labels are safe, not broken.** A chunk with no label is *not* bucketed
into a group and not counted as one. It is excluded from the measured share and
tallied separately as `unlabelled_share`. An arbitrary unlabelled corpus can
therefore be mixed in as background without corrupting any number: the measured
shares degrade to "these hits were not things we have labels for" instead of
silently miscounting.

**To measure a different attribute**, set your key in `attrs` at corpus-build
time and pass `attr="your_key"` to the metric. Nothing in `bias/ratio.py` is
specific to any one attribute.

## Protocol seams

The three swappable stages are declared as `typing.Protocol`s. A Protocol is
**structural**: any class with matching methods satisfies it automatically, with
no base class to inherit and no registration step. `HashEmbedder` does not import
or subclass anything to be a valid `Embedder`: it simply has `name` and `embed`.

```python
class Embedder(Protocol):
    @property
    def name(self) -> str: ...
    def embed(self, texts: list[str]) -> np.ndarray: ...   # unit-normalised rows

class Retriever(Protocol):
    @property
    def name(self) -> str: ...
    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]: ...

class Generator(Protocol):
    @property
    def name(self) -> str: ...
    def generate(self, query: str, contexts: list[RetrievedChunk]) -> RagAnswer: ...
```

**Why this shape.** The forum's recurring question is "what does this stage cost
us?", which requires holding everything else fixed while replacing one component.
Narrow interfaces make that a one-line change: `run_study` accepts any
`Retriever`, so comparing dense against MMR against 4-bit quantised search needs
no change to the metric, the corpus or the runner.

**Why `name` is part of the interface.** It is not decoration. Every results file
records `config.retriever` and `config.embedder` from these properties, so a
figure can always be traced back to the components that produced it, and a run
accidentally made with an offline stub is identifiable after the fact.

**Contracts the type signatures cannot express**, which an implementation must
honour:

- `Embedder.embed` returns **unit-normalised** rows. `VectorStore` uses a plain
  inner product as cosine similarity and would silently return wrong rankings
  otherwise. Use the `l2_normalise` helper.
- `Retriever.retrieve` returns results **sorted by descending score**, with
  `rank` set to the 0-based position. Metrics slice by prefix and trust the order.
- `Generator.generate` sets `cited_ranks` to 0-based indices into the `contexts`
  it was given. `parse_citations` handles this, including discarding references
  to passages that were never supplied.

### Offline mode

`HashEmbedder` and `EchoGenerator` satisfy the protocols without a network, so
`--offline` exercises the entire pipeline with no endpoint. `HashEmbedder` hashes
words into buckets and has **no semantic content**: use it to check plumbing,
never to produce a result. Any results file whose `config.embedder` reads
`hash-256` is a smoke test, not a finding.

## On-disk layout

Everything under `data/` is generated and gitignored.

```
data/
├── corpus/     cached source material (expensive to fetch, cheap to reuse)
├── index/      one embedded store per corpus variant
│   └── variant_R/    chunks.parquet · vectors.npy · meta.json
└── results/    one self-describing JSON per study run
```

A store is three files: `chunks.parquet` (text, provenance and `attrs`),
`vectors.npy` (float32, unit-normalised) and `meta.json` (embedder name,
dimension, count).

`chunks.parquet` and `vectors.npy` are **row-aligned**: row *i* of one belongs to
row *i* of the other, validated on construction. This is the fix for the 260615
pipeline, which stored vectors only and so could return an index pointing at
nothing.

Delete `data/index/` when changing embedding model: a store built with one model
cannot be searched with another. `VectorStore.search` raises a dimension-mismatch
error saying exactly that rather than returning nonsense. `data/corpus/` survives
such a rebuild, so only the embedding is paid for again.

## CLI

```
workshop-rag [--offline] <command>

  build-corpus   fetch source data, sample a variant, embed, save a store
  query          run one query through retrieval (+ generation if configured)
  study          run the bias study on a variant, write results
  show           print a saved results file
```

Meeting scripts are thin wrappers that call `cli.main()`. The logic lives in the
package; a meeting folder only sequences it and renders figures.

## Tests

74 tests, no network. External data is passed in as fixtures rather than
fetched.

| File | Covers |
|---|---|
| `test_chunking.py` | no word is lost, overlap is exact, over-long windows split rather than truncate |
| `test_store.py` | row alignment, exact cosine ordering, parquet round trip with typed `attrs` |
| `test_ratio.py` | the metric's arithmetic, scale-freeness, both refusal rules, relevant-set filtering |
| `test_biographies.py` | corpus variants preserve or equalise the split, cannot invent people, person-level pooling |
| `test_retrieval.py` | DetGreedy's prefix guarantee, that it never invents or drops candidates, MMR and quantised search |
| `test_study.py` | person-deduplication, the trade-off sweep's endpoints, tercile restriction on both sides of the ratio, nDCG |

`test_ratio.py` is the important one: every case pins a property whose correct
answer is known by construction, because that file carries the study's claims.

## Conventions

- **Meeting folders** are `YYMMDD-topic/`. A README covers how to run it and what
  comes out; where the method needs arguing, a METHOD.md covers why.
- **`make lint`** runs codespell, `ruff check --fix`, `ruff format` and
  basedpyright over `src`, `tests`, `devtools`, reformatting in place. Meeting
  scripts are deliberately out of scope.
- **basedpyright runs clean**: zero errors *and* zero warnings. The three
  `reportUnknown*` rules are disabled in `pyproject.toml` because they fire only
  on values flowing out of numpy/pandas/pytest stubs; every rule that checks our
  own annotations stays on.
- **Results files are self-describing**: retriever, embedder, k values, seed and
  corpus counts sit alongside the numbers.

## Extending it

**Measure a different attribute.** The metric takes an `attr` argument. Set your
key in `Document.attrs` at build time and pass `attr="your_key"`; the metric
itself is attribute-agnostic.

**Add a retriever.** Implement the `Retriever` protocol and register it in
`cli._retriever`. `MMRRetriever` is the shortest example of one that wraps
another.

**Add a corpus.** Emit `Document`s with whatever labels the study needs in
`attrs`. `biographies.py` is the worked example.

**Add a meeting.** Create `03_workshop/YYMMDD-topic/` with driver scripts that
call into the package. Resist putting logic there; if a second meeting could use
it, it belongs in `src/`.
