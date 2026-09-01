# Meeting 260901 — Bias im RAG

Code for the empirical part of the session. The slide outline is the reference;
this folder produces the numbers behind **Teil B (Ergebnisse)** and the material
for **Teil D (Selbstkritik)**.

## What is measured

**A = p_k / p₀**, per occupation and per gender.

- **p₀** — the base rate in the *relevant set*: the share of a group among the
  corpus people who actually hold the occupation being asked about.
- **p_k** — that group's share of the top-k.
- **A = 1** neutral, **> 1** amplified, **< 1** suppressed.

A ratio, not a difference of shares, because a ratio is scale-free in p₀. Ten
points of gap means something very different against a 50% base rate than
against a 8% one, and variants R and K would not otherwise be comparable.

k = 10 is the headline, k = 100 the robustness check. Both are prefixes of the
*same* ranking, so they cannot disagree for incidental reasons.

## The corpus

German Wikipedia biographies, labelled from Wikidata: **P21** (gender) and
**P106** (occupation). Populations come from [QLever](https://qlever.dev)
rather than the official WDQS endpoint — WDQS times out at 60 s on an occupation
the size of *Schauspiel*, QLever returns the full 61 k rows in about a second.
That matters: with the whole population in hand, **p₀ is an exact census, not an
estimate from a truncated sample.**

Populations as of the last run:

| Occupation | n (dewiki) | Frauen | Männer | andere |
|---|---:|---:|---:|---:|
| Schauspiel (Q33999) | 61 511 | 43.1 % | 56.6 % | 0.3 % |
| Fußball (Q937857) | 80 144 | 7.7 % | 92.3 % | 0.0 % |
| Politik (Q82955) | 139 508 | 12.4 % | 87.5 % | 0.0 % |
| Literatur (Q36180) | 84 093 | 23.2 % | 76.7 % | 0.2 % |
| **Model (Q4610556)** | 5 507 | **79.9 %** | 18.8 % | 1.3 % |
| **combined** | **370 763** | **19.93 %** | **79.95 %** | **0.12 %** |

The combined split reproduces the ~82 / 18 / <1 figure quoted in the Kritik
section, measured rather than cited. **Model** is the *Gegenprobe* occupation
(outline §9): women are the clear majority there, which separates a popularity
effect from a gender-association effect.

### Two variants

- **R — realistisch.** Each occupation keeps its true split. p₀ is whatever
  Wikidata contains.
- **K — 50/50.** The larger of female/male is downsampled per occupation until
  p₀ = 0.5. Any skew that survives is the pipeline's, since the corpus can no
  longer explain it.

`other` is carried at its natural size in K rather than inflated. There are not
enough people to balance it, and pretending otherwise would fabricate precision.

## Running it

```bash
cp .env_example .env        # OPENAI_API_BASE / _API_KEY / _EMBEDDING_MODEL

uv run workshop-rag build-corpus --variant R --per-occupation 400
uv run workshop-rag build-corpus --variant K --per-occupation 400
uv run workshop-rag study --variant R
uv run workshop-rag study --variant K
uv run python 03_workshop/260901-rag-bias/03_make_figures.py
```

Wikidata populations and article extracts are cached under `data/corpus/`, so
only the first build pays for them. Add `--offline` to exercise the plumbing with
hash embeddings.

> **`--offline` output is not a result.** `HashEmbedder` is a hashed word bag with
> no semantic content. It proves the pipeline runs; it says nothing about any
> embedding model. Every reported number needs a real endpoint.

| Variable | Meaning |
|---|---|
| `--variant R\|K` | corpus variant |
| `--per-occupation` | people sampled per occupation (default 400) |
| `--ks 10,100` | k values; the first is the headline |
| `--retriever` | `dense`, `mmr`, `turbovec-{2,3,4}` |
| `--seed` | sampling and bootstrap seed |

## Outputs

- `data/results/study_R.json`, `study_K.json` — every number, including the
  per-query breakdown and the reason any CI is missing.
- Figures in this folder:
  - `fig_amplification_{R,K}_k{10,100}.png` — A per occupation and group, with CIs.
  - `fig_base_vs_topk_*.png` — p₀ against p_k, before the division.
  - `fig_variants_k10.png` — R against K side by side.
  - `fig_wording_*.png` — the same question in three phrasings (§10).

## Deliberate refusals to report

Both are in the code, not just the slides:

- **A group with fewer than 30 people in the pool gets no confidence interval** —
  only its raw n, and a stated reason. Resampling four people yields an interval,
  but not an honest one. This is the non-binary case from §13: `other` is 0.12 %
  of the corpus.
- **p₀ = 0 yields `A = null`, never infinity.** A group absent from the pool
  cannot be amplified by retrieval.

## Known limitations

Material for Gruppenarbeit 2 — these are properties of *this* measurement, not
of RAG:

- **The bootstrap resamples retrieved slots, holding p₀ fixed.** p₀ is a census,
  so the uncertainty being quantified is in what got retrieved. Slots within one
  query are not independent, which makes the interval mildly optimistic.
- **Person-level, not chunk-level.** A biography split into several chunks counts
  once, in both p₀ and p_k. Without that, long articles would inflate their own
  group.
- **Only the lead section** is indexed, not the full article, and German
  biography leads are short (median ~170 characters). This is forced by the
  MediaWiki API: `exintro` is mandatory once `exlimit > 1`, and any other
  extract mode returns text for only the first page of each batch. Documents are
  therefore much shorter and more uniform than a real corpus, and article length
  is *not* yet controlled for as a covariate (§10).
- **Articles under 120 characters are dropped**, which is a selection on length.
  `build-corpus` prints the survival rate per gender so the size of that
  selection is visible; if it is not gender-neutral, p₀ in the corpus has moved
  away from p₀ in Wikidata.
- **Gender is a three-way bucket** from P21. Wikidata allows 36 values; everything
  outside the binary is collapsed into `other`.
- **P106 is multi-valued.** A person who is both actor and politician appears in
  both strata; the strata are not disjoint.
- **Occupation membership comes from Wikidata, not from the article text.** The
  relevant set is therefore an editorial artefact of Wikidata's coverage.

## Not implemented

Cut for time, and named here so the slides do not over-claim:

- **DetGreedy** and the A-versus-nDCG trade-off curve (§11). What exists is
  `MMRRetriever`, which is *relevance* diversification — the very thing the
  outline warns is a different meaning of "Reranker". It is not a fairness-aware
  reranker and should not be presented as one.
- **Article length as a covariate**, and the second-embedding-model replication
  (§10). The model swap is one env variable, but no sweep driver exists.
- **Generation** (§13) is not measured, consistent with the outline treating it
  as an acknowledged gap.
