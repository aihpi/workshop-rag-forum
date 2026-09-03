# Meeting 260901: Bias im RAG

Code for the empirical part of the session: it produces the numbers behind
**Teil B (Ergebnisse)** and the material for **Teil D (Selbstkritik)**.

- **[METHOD.md](METHOD.md)**: what is measured and why. The data sources, the
  R/K corpus variants, the metric $A = p_k/p_0$, the nDCG and length-tercile
  additions, and the reasoning behind all of it.
- **This file**: how to run it, what comes out, and what not to trust.

## In one paragraph

For each occupation we ask a question three ways, retrieve the top-$k$, and
compare each gender's share of the hits against its share of the corpus people
who actually hold that occupation. That ratio is $A$: 1 is neutral, below 1 means
the retriever surfaces the group less than availability predicts. The corpus is
German Wikipedia biographies labelled from Wikidata, built twice: once with the
real gender split (**R**) and once forced to 50/50 (**K**), so that a skew in K
cannot be blamed on the corpus.

Three things are reported alongside $A$, from the same retrieval:
**nDCG@$k$** against binary occupation relevance, so an intervention can be
priced; **$A$ inside article-length terciles**, which tests whether a preference
for longer articles explains the skew; and a **DetGreedy sweep** from no
correction to exact parity, which prices what parity costs in nDCG. See
[METHOD.md](METHOD.md#beyond-the-headline-number).

## Running it

```bash
cp .env_example .env        # OPENAI_API_BASE / _API_KEY / _EMBEDDING_MODEL

uv run python 03_workshop/260901-rag-bias/01_build_corpus.py   # both variants
uv run python 03_workshop/260901-rag-bias/02_run_study.py      # both variants
uv run python 03_workshop/260901-rag-bias/03_make_figures.py
```

Or one step at a time via the CLI:

```bash
uv run workshop-rag build-corpus --variant R --per-occupation 400
uv run workshop-rag study --variant R --ks 10,100
uv run workshop-rag show --variant R
```

Wikidata populations and article extracts are cached under `data/corpus/`, so
only the first build pays for them. A rebuild after changing embedding model
re-embeds but re-fetches nothing.

> **`--offline` output is not a result.** `HashEmbedder` is a hashed word bag
> with no semantic content. It proves the pipeline runs; it says nothing about
> any embedding model. Every reported number needs a real endpoint.

### Options

| Variable | Meaning |
|---|---|
| `--variant R\|K` | corpus variant (script equivalent: both are built in turn) |
| `--per-occupation` | people sampled per occupation (default 400) |
| `--ks 10,100` | k values; the first is the headline |
| `--retriever` | `dense`, `mmr`, `detgreedy`, `turbovec-{2,3,4}` |
| `--no-tradeoff` | skip the DetGreedy vs. nDCG sweep |
| `--no-covariate` | skip the article-length tercile analysis |
| `--seed` | sampling and bootstrap seed |
| `--offline` | hash embeddings, no endpoint |

Script wrappers read `PER_OCCUPATION`, `KS`, `RETRIEVER` and `OFFLINE` from the
environment.

## Outputs

- `data/results/study_R.json`, `study_K.json`: every number, including the
  per-query breakdown, `off_topic_share`, and the reason any confidence interval
  is missing. Per occupation stratum:

  | Key | Holds |
  |---|---|
  | `by_k` | $A$, $p_0$, $p_k$ and the CI per group, at each $k$ |
  | `ndcg` | nDCG@$k$ of the unreranked run, at each $k$ |
  | `by_length_tercile` | $A$ recomputed inside each length tercile, plus the tercile edges |
  | `length_profile` | median article length per group, the difference the terciles control for |
  | `tradeoff` | one row per DetGreedy step: `lambda`, targets, $A$, $p_k$, nDCG |
  | `k_fully_reached` | which $k$ survived person-deduplication, so a short ranking is not read as a result |

- Figures in this folder:
  - `fig_amplification_{R,K}_k{10,100}.png`: $A$ per occupation and group, with CIs.
  - `fig_base_vs_topk_*.png`: $p_0$ against $p_k$, before the division.
  - `fig_variants_k10.png`: R against K side by side.
  - `fig_wording_*.png`: the same question in three phrasings.

  The tercile and trade-off blocks have no figure yet; they are in the results
  file only.

Results files record the retriever, embedder, k values, seed and corpus counts,
so a figure can always be traced to the run that made it.

## Known limitations

Material for Gruppenarbeit 2. These are properties of *this measurement*, not of
RAG in general.

- **The bootstrap resamples retrieved slots, holding $p_0$ fixed.** $p_0$ is a
  census, so the uncertainty quantified is in what got retrieved. Slots within
  one query are not independent, which makes the interval mildly optimistic.
- **Only the lead section is indexed**, not the full article, and German
  biography leads are short (median ~170 characters). Forced by the MediaWiki
  API: `exintro` is mandatory once `exlimit > 1`, and any other extract mode
  returns text for only the first page of each batch. Documents are therefore
  shorter and more uniform than a real corpus.
- **Articles under 120 characters are dropped**, a selection on length.
  `build-corpus` prints the survival rate per gender so the size of that
  selection is visible. On the current sample 72.6 % of women against 75.2 % of
  men, so p₀ in the corpus sits slightly below p₀ in Wikidata.
- **The sample is 400 people per occupation**, drawn with a fixed seed from
  populations of 5 500–139 000. Results are subject to sampling noise beyond what
  the bootstrap covers.
- **Gender is a three-way bucket** from P21. Wikidata allows 36 values;
  everything outside the binary is collapsed into `other`.
- **Occupation strata are not disjoint.** P106 is multi-valued, so a person who
  is both actor and politician is in both relevant sets.
- **Occupation membership comes from Wikidata, not from the article text**, so
  the relevant set is an editorial artefact of Wikidata's coverage.
- **Nothing here has run against a real embedding model yet.** No `.env` was
  available during development, so all verification used `HashEmbedder` and this
  folder ships no figures.

Two further caveats belong to the additions rather than to $A$:

- **nDCG here uses binary occupation relevance**, which cannot say that one actor
  is a better answer than another. Read it as "how much on-topic material stayed
  near the top", not as a general IR score.
- **A tercile analysis needs spread in article length.** Where the lengths are
  too clumped to cut into three non-empty parts, the block reports `degenerate`
  with its reason instead of a number.

For what is deliberately *not* implemented (the second-embedding-model
replication, generation bias) see the Scope section of [METHOD.md](METHOD.md).
