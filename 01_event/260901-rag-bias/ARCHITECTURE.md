# Architecture: the 260901 code

How the code of this meeting is organised and why. For the method see
[METHOD.md](METHOD.md), for commands and outputs [README.md](README.md), for the
repository as a whole and how a meeting fits in
[development.md](../../development.md).

Two packages in `src/` are deliberately kept apart:

1. **A RAG pipeline**, `workshop_rag_forum`. Every stage is swappable, which is
   the whole point: a meeting's question is usually "what changes if I swap
   *this* stage?" It knows nothing about the study.
2. **The study**, `rag_bias`. It imports the pipeline, never the reverse.

The pipeline lives next to the study because the study is its only user. When a
second meeting needs it, move it to a workspace member of its own at the root
and point both meetings at it. The one line that depends on where it sits is
`REPO_ROOT` in `config.py`, which counts folder levels up to the repository root
for `.env` and `data/`.

## The pipeline package

`src/workshop_rag_forum/`:

| Module | What it does |
|---|---|
| `types.py` | The four dataclasses that cross module boundaries (`Document`, `Chunk`, `RetrievedChunk`, `RagAnswer`) plus the `attrs` key names. Everything else depends on this and it depends on nothing. |
| `config.py` | Reads `.env` once into a `Settings` object: endpoint URL, API key, model names, chunking parameters, and the `data/` path layout. Fails loudly on a missing chat model rather than guessing one. |
| `chunking.py` | Splits a document into overlapping word windows. Never truncates: an over-long window is split again on a word boundary, so no source text is silently lost. |
| `embedding.py` | Turns text into unit-normalised vectors. `OpenAIEmbedder` talks to any OpenAI-compatible endpoint and shrinks-and-retries when the endpoint rejects an input as too long; `HashEmbedder` is a deterministic offline stand-in. |
| `store.py` | `VectorStore` holds chunks and their vectors **row-aligned**, does exact cosine top-k, and persists to parquet + `.npy`. Validates the alignment on construction. |
| `retrieval.py` | Query text in, ranked `RetrievedChunk`s out. `DenseRetriever` (plain cosine), `MMRRetriever` (diversity reranking), `TurboVecRetriever` (quantised search with turbovec, the 260615 topic). |
| `generation.py` | Builds a numbered-context prompt, calls the chat model, and parses the `[n]` citations back out, so it is recorded which passages the answer actually used. |
| `pipeline.py` | `RagPipeline`: a retriever plus an optional generator. Generation is optional so retrieval-only studies need no chat model. |

## The study package

`src/rag_bias/` imports the pipeline above and adds what only the bias study
needs; its method is documented in [METHOD.md](METHOD.md).

| Module | What it does |
|---|---|
| `biographies.py` | Builds the study corpus: German Wikipedia biographies labelled from Wikidata, in the R and K variants. |
| `rerank.py` | `DetGreedyRetriever` and `rerank_detgreedy`: fairness-aware reranking, a minimum share per group in every prefix. |
| `cli.py` | The `rag-bias` command: `build-corpus`, `query`, `study`, `show`. |
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
rag-bias [--offline] <command>

  build-corpus   fetch source data, sample a variant, embed, save a store
  query          run one query through retrieval (+ generation if configured)
  study          run the bias study on a variant, write results
  show           print a saved results file
```

The command comes from the `rag-bias` workspace member. The 260901 driver
scripts are thin wrappers that call `rag_bias.cli.main()`; the logic lives in the
packages, and a script only sequences it and renders figures.

## Tests

74 tests, no network. External data is passed in as fixtures rather than
fetched. All of them sit in `tests/`; `uv run pytest` from the repository root
runs them.

| File | Covers |
|---|---|
| `test_chunking.py` | no word is lost, overlap is exact, over-long windows split rather than truncate |
| `test_store.py` | row alignment, exact cosine ordering, parquet round trip with typed `attrs` |
| `test_retrieval.py` | dense and MMR retrieval, citation parsing, the pipeline with and without a generator |
| `test_ratio.py` | the metric's arithmetic, scale-freeness, both refusal rules, relevant-set filtering |
| `test_biographies.py` | corpus variants preserve or equalise the split, cannot invent people, person-level pooling |
| `test_rerank.py` | DetGreedy's prefix guarantee, that it never invents or drops candidates, target normalisation |
| `test_study.py` | person-deduplication, the trade-off sweep's endpoints, tercile restriction on both sides of the ratio, nDCG |

`test_ratio.py` is the important one: every case pins a property whose correct
answer is known by construction, because that file carries the study's claims.

## Conventions

- **Results files are self-describing**: retriever, embedder, k values, seed and
  corpus counts sit alongside the numbers.
- **Driver scripts stay thin.** `01_…03_*.py` sequence the CLI and render
  figures; logic lives in the packages, where `make lint` and the tests reach it.

## Extending it

**Measure a different attribute.** The metric takes an `attr` argument. Set your
key in `Document.attrs` at build time and pass `attr="your_key"`; the metric
itself is attribute-agnostic.

**Add a retriever.** Implement the `Retriever` protocol. A general one goes in
`workshop_rag_forum/retrieval.py`, one tied to a single study in that meeting's
package (as `rag_bias/rerank.py` does). Register it in the meeting's
`cli._retriever`. `MMRRetriever` is the shortest example of one that wraps
another.

**Add a corpus.** Emit `Document`s with whatever labels the study needs in
`attrs`. `rag_bias/biographies.py` is the worked example.

**Reuse the pipeline in another meeting.** Move `workshop_rag_forum` out into a
workspace member of its own rather than depending on `rag-bias`, which would
drag the study's dependencies along. How a meeting joins the workspace is in
[development.md](../../development.md).
