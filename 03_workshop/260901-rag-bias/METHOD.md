# Method: Bias im RAG (260901)

What this session measures and why the measurement is built the way it is. For
commands, outputs and known limitations see [README.md](README.md); for the
pipeline this sits on top of see [ARCHITECTURE.md](../../ARCHITECTURE.md).

The slide outline is the reference. This document covers **Teil A §5–6** (the
dataset and how we measure) together with **§10–11** (the covariate control and
the reranking trade-off), and supplies the reasoning behind **Teil B**.

## Where the data comes from

Two external sources, doing two different jobs.

### Wikidata, for the labels

Wikidata is a structured database of *items*, each with an identifier like
`Q33999`, described by statements built from numbered *properties*:

| Identifier | Meaning |
|---|---|
| `Q5` | the item "human", used to restrict the query to people |
| **`P21`** | *sex or gender*. Its value is itself an item: `Q6581072` female, `Q6581097` male, and roughly 34 others |
| **`P106`** | *occupation*. Also item-valued: `Q33999` actor, `Q937857` footballer, `Q82955` politician, `Q36180` writer, `Q4610556` model |

So "P21 gender" is shorthand for *the gender statement on this person's Wikidata
item*, and "P106 occupation" for *the occupation statement*. Both are
**multi-valued** (a person can be both actor and politician), which the code has
to respect rather than flatten.

Queries go to **[QLever](https://qlever.dev)** rather than Wikidata's own SPARQL
endpoint. The official service caps queries at 60 seconds and times out on an
occupation the size of *Schauspiel*; QLever returns the full 61 511-row result in
about a second. That is not merely convenient: having the **whole** population
rather than a truncated slice is what makes the base rate an exact census instead
of an estimate, and the base rate is half the metric.

Measured populations (people with a German Wikipedia article):

| Occupation | n | Frauen | Männer | andere |
|---|---:|---:|---:|---:|
| Schauspiel (`Q33999`) | 61 511 | 43.1 % | 56.6 % | 0.3 % |
| Fußball (`Q937857`) | 80 144 | 7.7 % | 92.3 % | 0.0 % |
| Politik (`Q82955`) | 139 508 | 12.4 % | 87.5 % | 0.0 % |
| Literatur (`Q36180`) | 84 093 | 23.2 % | 76.7 % | 0.2 % |
| **Model (`Q4610556`)** | 5 507 | **79.9 %** | 18.8 % | 1.3 % |
| **combined** | **370 763** | **19.93 %** | **79.95 %** | **0.12 %** |

The combined split reproduces the ~82 / 18 / <1 figure quoted in the Kritik
section, measured here rather than cited.

**Model** is the *Gegenprobe* occupation (§9): women are the clear majority.
Without it, an all-male-majority set of occupations cannot distinguish a
retriever that favours the *majority* from one that favours *men*.

### German Wikipedia, for the text

Wikidata items link to their article, and the MediaWiki API returns each
article's **lead section**. Only the lead: the API requires `exintro` as soon as
more than one page is requested per call, so full text would mean one request per
person. German biography leads are short, median ~170 characters, which is a
real constraint on how much the retriever has to work with.

## The two corpus variants

The experiment's central control.

- **R, realistisch.** Each occupation keeps its true gender split. The base rate
  is whatever Wikidata contains: 43 % women among actors, 8 % among footballers.
- **K, 50/50.** Within each occupation the larger of female/male is downsampled
  until the split is even.

**K exists to remove one explanation.** In R, a male-heavy top-10 might simply
reflect a male-heavy corpus: the pipeline could be behaving perfectly and still
return mostly men. In K the corpus cannot explain it, so whatever skew survives
belongs to the pipeline. That is what makes §7's claim ("ist jede Schieflage im
Ergebnis der Pipeline zuzurechnen") defensible rather than rhetorical.

Both variants are built from the same populations with the same seed and differ
only in sampling.

The `other` bucket is carried at natural size in K rather than inflated: there
are not enough non-binary people in the data to balance it, and padding it would
fabricate precision.

## Build and measurement flow

```
① Wikidata / QLever                    ② de.wikipedia API
   "all humans with P106 = Q33999,        "lead section of
    grouped by P21"                        each linked article"
        │  61 511 people, exact                │
        ▼                                      │
   fetch_population                            │
        │                                      │
        ▼                                      │
   sample_population  ── variant R or K        │
        │  400 people per occupation           │
        ▼                                      ▼
                     build_documents ◄─── fetch_extracts
                            │  Document: text + P21/P106 labels in .attrs
                            ▼
                     chunk_documents
                            │  Chunk[]: labels copied onto each
                            ▼
   Embedder ────────► VectorStore.build
                            │
                     data/index/variant_X/
                            │
        ┌───────────────────┴───────────────────┐
        ▼                                       ▼
   Retriever                              pool_groups
   top-k for each query phrasing          the relevant set → p₀
        │                                       │
        └──────► stratum_amplification ◄────────┘
                            │  A = p_k/p₀, bootstrap CI
                            ▼
                  data/results/study_X.json ──► figures
```

Three query phrasings per occupation (generic masculine, feminine, and
gender-neutral: *"Bekannte Schauspieler"* / *"Schauspielerinnen"* / *"Personen im
Schauspiel"*) are kept as separate queries so the wording effect stays visible
per query instead of being averaged away (§10).

## The metric

### What it is trying to capture

Suppose a query returns ten footballers and one is a woman. Is that biased? The
number alone says nothing, because only about 8 % of footballers in the corpus
are women, and one in ten is roughly what *anything* drawing fairly from that
pool would return. The question is never "what share came back?" but **"what share
came back compared with what was available?"**

So the metric is a comparison against availability:

$$
A = \frac{p_k}{p_0}
$$

$$
p_0 = \frac{\text{people of the group in the relevant set}}{\text{people in the relevant set}}
$$

$$
p_k = \frac{\text{hits of the group in the top-}k}{\text{hits in the top-}k}
$$

The **relevant set** is the corpus people who actually hold the occupation the
query asks about: for *"Bekannte Schauspieler"*, the actors. $p_0$ is computed
over that set, not over the whole corpus.

| Value | Meaning |
|---|---|
| $A = 1$ | neutral: the top-$k$ mirrors what was available |
| $A > 1$ | amplified: the group appears more than availability predicts |
| $A < 1$ | suppressed: less than availability predicts |

$A = 0.4$ means the group is retrieved at 40 % of its own base rate.

### Why a ratio and not a difference

The obvious alternative is the gap $p_k - p_0$. It misleads here, because the
same gap means very different things at different base rates. Suppose retrieval
halves a group's presence:

| | $p_0$ | $p_k$ | gap | $A$ |
|---|---:|---:|---:|---:|
| Schauspiel | 0.43 | 0.215 | −0.215 | 0.5 |
| Fußball | 0.08 | 0.040 | −0.040 | 0.5 |

The gap calls the first case five times worse; the ratio correctly reports
identical relative treatment. Since variants R and K deliberately have
*different* base rates, only a scale-free measure lets their results be compared
at all.

$k = 10$ is the headline and $k = 100$ the robustness check.

### The confidence interval

Every $A$ carries a percentile bootstrap interval. The resampling is over
**retrieved slots**, with $p_0$ held fixed. $p_0$ is a census of the corpus pool,
not a sample, so the uncertainty being quantified is in *what got retrieved*.

Slots within a single query are not independent, which makes the interval mildly
optimistic. Stated here rather than hidden.

## Three invariants worth knowing

Each of these, if broken, still produces numbers that look entirely reasonable.
That is exactly why they are worth naming.

### 1. $p_k$ and $p_0$ must describe the same population

Retrieval runs over the **whole** corpus, so a query for actors also returns
footballers and politicians. If those hits counted towards $p_k$ while $p_0$ was
computed over actors only, the ratio would compare two different populations and
mean nothing.

*Concretely:* footballers are ~92 % male. Let them leak into an actor query's
$p_k$ and women look suppressed among actors, when in truth the retriever simply
drifted off-topic. `stratum_amplification` therefore counts only hits inside the
relevant set, and reports the rest as `off_topic_share`, which doubles as a
retrieval-quality signal.

### 2. Counting is per person, not per chunk

A long biography is split into several chunks, and several of them can land in
one top-$k$.

*Concretely:* if a 5-chunk article about one man occupies three of ten slots, a
naive count records "three men retrieved" for one person, and long articles
inflate their own group. Article length is not gender-neutral, so that alone
would manufacture a bias signal. `dedupe_by_person` collapses a ranking to its
best-ranked chunk per person before anything is counted, and `pool_groups`
deduplicates by `doc_id` so nobody is double-counted in $p_0$ either.

### 3. Every $k$ is a prefix of one ranking

Retrieval happens **once**, at the largest $k$; smaller values slice that same
result.

*Concretely:* running the retriever twice, once for $k=10$ and once for $k=100$,
would let the two disagree because of caching, ordering or endpoint
nondeterminism rather than because of $k$. Slicing one ranking guarantees any
difference between $k=10$ and $k=100$ is a real depth effect.

## Two refusals to report

"Refusal" here means the code **declines to output a number it could easily
compute**, because computing it would mislead. Both are enforced in
`bias/ratio.py`, not merely mentioned on a slide. A reader of the results file
sees an explicit absence with a reason, never a fabricated figure.

### No confidence interval for a very small group

A bootstrap interval *can* be computed from four people. It will be narrow,
symmetric and completely unjustified: it describes resampling noise in a handful
of rows, not uncertainty about a population.

So when a group has fewer than **`MIN_N_FOR_CI = 30`** people in the relevant
set, the interval is omitted and the results file records the count and the
reason instead:

```json
"amplification_ci95": { "other": null },
"ci_suppressed":      { "other": "n=5 < 30" }
```

This is the non-binary case from §13. Across the corpus `other` is 0.12 % of
people, so its $A$ is reported as a point value with its $n$ visible, and the
reader can judge it, exactly what the outline asks for ("das tatsächliche n,
ohne Konfidenzintervall").

### No infinity when the group is absent

If a group has nobody in the relevant set then $p_0 = 0$ and $A = p_k/0$ is
undefined. Returning infinity, or letting a division error escape, would read
as infinite amplification. The truthful statement is that the question does not
apply: retrieval cannot amplify a group that is not in the pool. So $A$ is
`null`, annotated `"absent from pool"`.

The distinction the code preserves: **`null`** means *unanswerable*, while
**`0.0`** means *the group was in the pool and never retrieved*, a real and
serious finding.

## Beyond the headline number

Three measurements sit on top of $A$, computed from the same single retrieval so
they describe the same run rather than three runs that might differ for unrelated
reasons.

### Retrieval quality, so an intervention can be priced (§11)

Reranking for representation always costs relevance. Reporting the gain in $A$
without the loss in ranking quality would make every intervention look free, so
the study measures nDCG@$k$ on the same run.

Relevance here is **binary and objective**: a hit counts as relevant if the
person holds the occupation the query asked about, which Wikidata already states.
No human judgements and no LLM judge, which also means no judge to be biased.

The ideal ranking is taken from the same retrieved set, every relevant hit first.
That measures how well the *ordering* uses what retrieval found, which is the
right question when comparing a reranker against its own input: the candidate
pool is identical and only the order differs. It is a coarse definition, since it
cannot say that one actor is a better answer than another, so read this nDCG as
"how much on-topic material stayed near the top", not as a general IR score.

### Fairness-aware reranking, and the trade-off curve (§11)

Note the terminology trap the outline warns about. In RAG a "reranker" normally
means a *relevance* reranker, and `MMRRetriever` is a *diversity* one. DetGreedy
(Geyik et al. 2019) is neither: it enforces a **minimum representation per group
in every prefix** of the ranking, and is the only component here that targets
representation directly.

The algorithm walks the ranking position by position. Before filling position $i$
it computes each group's minimum required count, $\lfloor i \cdot t_g \rfloor$
for target share $t_g$. Any group below its minimum is starved, and the
best-scoring remaining candidate from the starved groups takes the slot;
otherwise the best-scoring candidate overall takes it. The prefix property is the
point: a top-100 that is fair only at rank 100 is not fair to anyone who reads
the first page.

Setting the targets to $p_0$ is a request for $A = 1$. The study sweeps a
parameter $\lambda$ from the ranking's own observed composition ($\lambda = 0$,
nothing to correct) to $p_0$ ($\lambda = 1$, exact parity), and records $A$ and
nDCG at each step. That curve is the answer to "what does parity cost here?",
measured rather than asserted. Because the rerank is a pure function over an
already-fetched ranking, the whole curve costs no extra retrieval.

### Article length as a covariate (§10)

A plausible innocent explanation for a low $A$: the retriever prefers longer
articles, and one group's articles happen to be shorter. That is still a real
effect on who gets found, but it is a *different* mechanism from the embedding
associating a query with a gender, and the two call for different fixes.

The control is **stratification, not regression**. The relevant set is cut into
length terciles and $A$ is recomputed inside each one, where the groups have
near-identical article lengths:

* $A$ moves to ~1 inside every tercile: length accounted for the whole effect.
* $A$ stays away from 1 inside the terciles: something other than length is at
  work.

Stratification is preferred deliberately. It assumes nothing about functional
form, it is readable without statistics, and it degrades the same way the main
metric does, reporting a cell's $n$ and no interval when the cell is too small.
Both sides of the ratio are restricted together: the pool for a tercile holds
only people in that tercile and the hits are filtered to the same tercile, since
restricting one side alone would reintroduce the population mismatch invariant 1
exists to prevent. A prior `length_profile` reports the median article length per
group, which answers whether there is any length difference to control for in the
first place, and a length distribution too clumped to cut into three non-empty
parts is reported as `degenerate` rather than quietly returning fewer terciles.

## Scope

Present: retrieval bias measurement end to end on real labelled data, for both
corpus variants and both $k$ values, plus the three additions above (nDCG,
DetGreedy with its trade-off curve, and the length terciles).

Absent, and named so the slides do not over-claim:

- **The second-embedding-model replication (§10).** The model swap is one
  environment variable, but no sweep driver exists, so nothing here shows whether
  a finding survives a change of embedding model.
- **Generation (§13).** The pipeline can generate and parses its own citations,
  but this study does not measure generation bias, consistent with the outline
  treating it as an acknowledged gap.
- **A causal account of *why* the embedding behaves as it does.** The study
  measures the effect and tests one candidate explanation for it, article length.
  It does not open the model.

Limitations of what *is* implemented (sampling, lead-section-only text, the
three-way gender bucket, non-disjoint occupation strata) are listed in
[README.md](README.md) alongside the results they qualify.
