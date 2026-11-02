<p align="center">
  <img src="00_aisc/img/logo_aisc_bmftr.jpg" alt="AISC / BMFTR">
</p>

# workshop-rag-forum

A forum for monthly meetings centred around **Retrieval-Augmented Generation (RAG)**.
Each meeting explores a different topic (embedding models, vector compression,
retrieval strategies, evaluation, etc.).

## The RAG forum at a glance

<p align="center">
  <img src="00_aisc/img/rag_illustration.png" width="640" alt="A RAG pipeline: documents are chunked and embedded into a vector database, a user query retrieves context, and an LLM composes the response">
</p>

A RAG system is a short pipeline, but almost every stage hides a knob worth turning.
Each meeting we pick one, dig in together, and compare problems, stacks, and ideas.


## Repository layout

```
src/workshop_rag_forum/   # the shared RAG pipeline, used by every meeting
  chunking, embedding, store, retrieval, generation, pipeline
tests/                    # pytest suite for src/
01_event/                 # one folder per meeting: YYMMDD-topic/
  260615-turbovec/        # vector compression; standalone scripts + pyproject.toml
  260901-rag-bias/        # retrieval bias; own package, tests + pyproject.toml
    src/rag_bias/         # biographies corpus, bias/ metrics, DetGreedy, `rag-bias` CLI
  261102-llm-wiki/        # LLM wiki instead of RAG, with starter skills; no code
devtools/                 # lint script behind `make lint` and CI
data/                     # corpora, indexes & results (gitignored)
.env_example              # copy to .env and fill in your endpoint + key
```

## The RAG pipeline

`src/workshop_rag_forum/` is a small, complete RAG system rather than a demo
script. Every stage sits behind a `Protocol`, which is what lets the meetings
compare stages against each other:

| Stage | Implementations |
|-------|-----------------|
| Embedding | `OpenAIEmbedder` (any OpenAI-compatible endpoint, incl. a LiteLLM proxy), `HashEmbedder` (deterministic, offline) |
| Store | `VectorStore`, with text, labels and vectors persisted **together**, exact cosine search |
| Retrieval | `DenseRetriever`, `MMRRetriever` (relevance diversification), `TurboVecRetriever` (quantised, reusing the 260615 index) |
| Generation | `OpenAIGenerator` (citation-grounded prompting), `EchoGenerator` (offline stub) |

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/):
the root project is the shared pipeline, and every meeting with code is a
member with its own `pyproject.toml` and dependencies. Code that only one
meeting needs lives in that meeting's folder and imports from the pipeline,
never the other way round. `make install` (`uv sync --all-packages --all-extras`)
installs everything into one `.venv`.

## Measuring retrieval bias

The 260901 meeting measures **A = p_k / p₀**, a group's share of the top-k
divided by its base rate in the relevant set, on German Wikipedia biographies
labelled from Wikidata. A ratio rather than a share gap, so it is scale-free in
the base rate. The same run also reports nDCG, A inside article-length terciles,
and what fairness-aware reranking costs in ranking quality.

```bash
cp .env_example .env      # OPENAI_API_BASE / _API_KEY / _EMBEDDING_MODEL

uv sync --all-packages    # installs the pipeline and the rag-bias package

uv run rag-bias build-corpus --variant R    # realistic gender split
uv run rag-bias build-corpus --variant K    # downsampled to 50/50
uv run rag-bias study --variant R --ks 10,100
uv run rag-bias show --variant R
```

Add `--offline` to exercise the pipeline with hash embeddings and no endpoint:
useful for checking the plumbing, never for a reported number.

## Meetings

| Date     | Topic     | Folder                        | Summary                                              |
|----------|-----------|-------------------------------|------------------------------------------------------|
| 26-06-15 | turbovec  | [`01_event/260615-turbovec/`](01_event/260615-turbovec/) | Illustrating turbovec vector compression vs. a float32 embedding baseline |
| 26-09-01 | rag-bias  | [`01_event/260901-rag-bias/`](01_event/260901-rag-bias/) | Bias im RAG: measuring A = p_k/p₀ across occupations, with a realistic and a 50/50 corpus |
| 26-11-02 | llm-wiki  | [`01_event/261102-llm-wiki/`](01_event/261102-llm-wiki/) | Das KISZ-Wiki: why the team keeps its own knowledge in an LLM-maintained wiki instead of RAG; slides and generic skills to start your own wiki |

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md): how the repository and the pipeline are
  organised. Module map, the `attrs` contract, the Protocol seams, on-disk layout.
- [01_event/260901-rag-bias/METHOD.md](01_event/260901-rag-bias/METHOD.md):
  the bias study's method. Data sources, corpus variants, and the metric.

## Setup

See [installation.md](installation.md) for installing uv and Python, and
[development.md](development.md) for development workflows. Copy `.env_example` to
`.env` and fill in your endpoint, key and model names before running a meeting's
scripts.

## References

- [AI Service Centre Berlin Brandenburg (KI-Servicezentrum)](https://hpi.de/ki-servicezentrum/)

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgements
<img src="00_aisc/img/logo_bmftr_de.png" alt="drawing" style="width:170px;"/>

The [AI Service Centre Berlin Brandenburg](http://hpi.de/kisz) is funded by the [Federal Ministry of Research, Technology and Space](https://www.bmbf.de/) under the funding code 01IS22092.
