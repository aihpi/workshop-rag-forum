# Meeting 260615 — turbovec: vector compression for RAG

**Date:** 2026-06-15 · **Venv:** `.venv_260615-turbovec`

## Goal

Illustrate **[turbovec](https://github.com/RyanCodrai/turbovec)**, a fast local vector
quantizer/index, and quantify *how much storage it saves* and *how much retrieval quality
it costs* compared to storing raw float32 embeddings.

In a RAG system every chunk of your corpus is stored as a high-dimensional embedding
vector. At scale this dominates memory/disk. turbovec implements Google Research's
**TurboQuant** — a data-oblivious quantizer (no training phase) with hand-written
NEON/AVX-512 kernels — and lets you store those vectors at **2, 3, or 4 bits per
dimension** instead of 32, while still searching them directly.

### What is being compared

- **Baseline:** raw embeddings from a locally hosted embedding model (**minilm-embedding**,
  served via an OpenAI-compatible API), stored as `float32` = **32 bits/dim**.
- **turbovec:** the *same* vectors quantized at **4-bit (8× smaller)**, **3-bit (~10.7× smaller)**
  and **2-bit (16× smaller)**. (turbovec supports bit-widths 2–4.)

> turbovec is **not** an embedding model — it compresses whatever vectors you give it.
> The compression ratio (8×–16×) is *independent* of the embedding model and dimension;
> only the absolute byte sizes and the retrieval recall depend on the data. minilm is chosen
> here purely because it is fast, which keeps the demo quick.

## Pipeline

All scripts are run from the repo root with the meeting's venv. The corpus and generated
vectors land in `data/` (gitignored).

| Step | Script | What it does |
|------|--------|--------------|
| 1 | `01_download_data.py` | Downloads whole parquet shards of German Wikipedia (`wikimedia/wikipedia`, `20231101.de`) into `data/dewiki/` until ~512 MB is reached (predictable, shard-granular). |
| 2 | `02_chunk_and_embed.py` | Splits articles into short chunks (≤256 tokens — the minilm input cap), embeds them through the minilm OpenAI-compatible endpoint, and saves `float32` vectors as `.npy` shards in `data/embeddings/`. Resumable; honours `MAX_CHUNKS`. |
| 3 | `03_compress_turbovec.py` | Loads the vectors, builds a `TurboQuantIndex` at 2/3/4-bit, writes each index to `data/index/`, measures on-disk size, and computes **recall@10** against an exact float32 brute-force search. Writes `data/results.json`. |
| 4 | `04_make_figures.py` | Reads `data/results.json` and renders the comparison figures (PNG) into this folder. |
| 5 | `05_benchmark_latency.py` | Times float32 brute-force vs turbovec search per bit-width on the embeddings and **merges latency** (ms/query, q/s, speed-up) into `data/results.json`. |
| 6 | `06_make_slides.py` | Builds the intro deck `turbovec_intro.pptx` (8 slides) on top of the AISC template, pulling numbers from `data/results.json`. Set `TEMPLATE_PPTX` to the template path. No PDF — export one from the `.pptx` if needed. |

## How to run

```bash
# from the repo root: /sc/projects/sci-aisc/workshop-rag-forum
cp .env_example .env          # then edit .env: set OPENAI_API_KEY / OPENAI_API_BASE

uv venv .venv_260615-turbovec --python 3.12
export UV_PROJECT_ENVIRONMENT=.venv_260615-turbovec
uv add turbovec openai python-dotenv datasets huggingface_hub numpy matplotlib tqdm pyarrow pandas

uv run python 03_workshop/260615-turbovec/01_download_data.py
uv run python 03_workshop/260615-turbovec/02_chunk_and_embed.py     # MAX_CHUNKS=2000 for a quick dry run
uv run python 03_workshop/260615-turbovec/03_compress_turbovec.py
uv run python 03_workshop/260615-turbovec/04_make_figures.py
uv run python 03_workshop/260615-turbovec/05_benchmark_latency.py
TEMPLATE_PPTX=path/to/aisc_template.pptx uv run python 03_workshop/260615-turbovec/06_make_slides.py
```

> The slide deck (`06_make_slides.py`) builds on the [PPTX skill](https://github.com/anthropics/skills/tree/main/skills/pptx)
> and an AISC template `.pptx`; it needs `python-pptx`. It produces `turbovec_intro.pptx` only.

### Useful environment variables

| Variable | Default | Meaning |
|----------|---------|---------|
| `TARGET_BYTES` | `512_000_000` | Download target for step 1 (bytes). |
| `MAX_CHUNKS` | unset (all) | Cap on number of chunks embedded in step 2 (use a small value for a dry run). |
| `CHUNK_WORDS` | `90` | Words per chunk (minilm caps each input at 256 tokens). |
| `MAX_CHARS` | `450` | Hard per-chunk char cap; `embed_batch` shrinks further and retries on a 413. |
| `EMBED_BATCH` | `32` | Chunks per embedding API request (the endpoint caps batches at 32). |
| `N_QUERIES` | `1000` | Held-out queries used for the recall evaluation. |
| `TOP_K` | `10` | k for recall@k. |
| `REPEATS` | `5` | Timed repeats per search in the latency benchmark (median is reported). |
| `BIT_WIDTHS` | `2,3,4` | turbovec bit-widths to evaluate (supported range 2–4). |

## Expected outputs

- `data/results.json` — sizes, compression ratios, and recall@10 per bit-width.
- Figures in this folder:
  - `fig_storage_size.png` — absolute store size: float32 baseline vs 2/3/4-bit.
  - `fig_compression_ratio.png` — compression factor vs float32.
  - `fig_recall.png` — recall@10 vs bit-width.
  - `fig_tradeoff.png` — storage-vs-recall trade-off scatter.

## Talking points for the meeting

- TurboQuant needs **no training/calibration** — unlike PQ/OPQ — so it fits streaming ingestion.
- Compression ratio is fixed by `bit_width`; the interesting question is the **recall cost**:
  4-bit (8×) is the high-fidelity sweet spot, 3-bit (~10.7×) a middle ground, 2-bit (16×) maximises savings.
- For a real corpus the float32 store grows linearly — extrapolate the per-vector savings to
  your production document count.
