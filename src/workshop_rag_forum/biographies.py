"""The study corpus: German Wikipedia biographies labelled from Wikidata.

People are selected by occupation (P106) and labelled by gender (P21), then
their German Wikipedia intro is fetched as the document text.

Two variants, as in the outline:

* **R** - realistic. The corpus keeps each occupation's true gender split, so the
  base rate p0 is whatever Wikidata actually contains.
* **K** - the majority group is downsampled until p0 = 0.5 per occupation, so any
  skew left in the top-k is the pipeline's doing and nothing else's.

Populations come from QLever rather than the official WDQS endpoint: WDQS times
out at 60s on occupations the size of "Schauspieler", while QLever returns the
full 61k-row population in about a second. Getting the *whole* population matters
- it makes p0 an exact count rather than an estimate from a truncated sample.
"""

from __future__ import annotations

import json
import random
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx

from .types import Document

QLEVER_ENDPOINT = "https://qlever.dev/api/wikidata"
WIKIPEDIA_API = "https://de.wikipedia.org/w/api.php"
USER_AGENT = "workshop-rag-forum/0.1 (HPI AI Service Centre; RAG bias forum)"

# P21 values. Everything outside the binary is bucketed together: on this corpus
# it is well under 1% (see the Kritik section of the meeting README), which is
# too few to bootstrap but not a reason to drop the people from the study.
GENDER_MALE = "Q6581097"
GENDER_FEMALE = "Q6581072"
GENDER_BUCKETS = {GENDER_FEMALE: "female", GENDER_MALE: "male"}
GENDER_OTHER = "other"
GROUPS = ["female", "male", GENDER_OTHER]

VARIANT_REALISTIC = "R"
VARIANT_BALANCED = "K"


@dataclass(slots=True)
class Occupation:
    """One P106 value, with the German query phrasings used to retrieve it."""

    qid: str
    label: str
    # Generic masculine / feminine / gender-neutral phrasing of the same request.
    # Kept as three separate queries so the wording effect is visible per query
    # rather than averaged away.
    queries: list[str] = field(default_factory=list)


# The Gegenprobe (outline section 9) needs an occupation where women are the
# majority; `model` is that case on this corpus.
DEFAULT_OCCUPATIONS = [
    Occupation(
        "Q33999",
        "Schauspiel",
        [
            "Bekannte Schauspieler",
            "Bekannte Schauspielerinnen",
            "Bekannte Personen im Schauspiel",
        ],
    ),
    Occupation(
        "Q937857",
        "Fußball",
        [
            "Bekannte Fußballspieler",
            "Bekannte Fußballspielerinnen",
            "Bekannte Personen im Fußball",
        ],
    ),
    Occupation(
        "Q82955",
        "Politik",
        [
            "Bekannte Politiker",
            "Bekannte Politikerinnen",
            "Bekannte Personen in der Politik",
        ],
    ),
    Occupation(
        "Q36180",
        "Literatur",
        [
            "Bekannte Schriftsteller",
            "Bekannte Schriftstellerinnen",
            "Bekannte Personen in der Literatur",
        ],
    ),
    Occupation(
        "Q4610556",
        "Model",
        [
            "Bekannte Models",
            "Bekannte weibliche Models",
            "Bekannte Personen im Modelbereich",
        ],
    ),
]


def _sparql(query: str, timeout: float = 90.0) -> list[dict[str, Any]]:
    response = httpx.post(
        QLEVER_ENDPOINT,
        content=query,
        headers={
            "User-Agent": USER_AGENT,
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()["results"]["bindings"]


def fetch_population(occupation: Occupation) -> list[dict[str, str]]:
    """Every dewiki-linked person with this occupation, with a gender bucket.

    Split into three queries because one unrestricted query over a large
    occupation is markedly slower than the parts.
    """
    people: list[dict[str, str]] = []
    seen: set[str] = set()
    clauses = [
        (f"?person wdt:P21 wd:{GENDER_FEMALE} .", "female"),
        (f"?person wdt:P21 wd:{GENDER_MALE} .", "male"),
        (
            "?person wdt:P21 ?gender . "
            f"FILTER(?gender != wd:{GENDER_FEMALE} && ?gender != wd:{GENDER_MALE})",
            GENDER_OTHER,
        ),
    ]
    for clause, bucket in clauses:
        rows = _sparql(f"""PREFIX wdt: <http://www.wikidata.org/prop/direct/>
PREFIX wd: <http://www.wikidata.org/entity/>
PREFIX schema: <http://schema.org/>
SELECT ?person ?article WHERE {{
  ?person wdt:P31 wd:Q5 ; wdt:P106 wd:{occupation.qid} .
  {clause}
  ?article schema:about ?person ; schema:isPartOf <https://de.wikipedia.org/> .
}}""")
        for row in rows:
            qid = row["person"]["value"].rsplit("/", 1)[-1]
            if qid in seen:
                continue  # a person with several non-binary P21 values
            seen.add(qid)
            people.append(
                {
                    "qid": qid,
                    "title": unquote(
                        row["article"]["value"].rsplit("/", 1)[-1]
                    ).replace("_", " "),
                    "gender": bucket,
                    "occupation": occupation.label,
                    "occupation_qid": occupation.qid,
                }
            )
    return people


def base_rates(people: list[dict[str, str]]) -> dict[str, float]:
    """Gender shares of a population - the p0 the study measures against."""
    total = len(people)
    if not total:
        return dict.fromkeys(GROUPS, 0.0)
    return {
        group: sum(1 for p in people if p["gender"] == group) / total
        for group in GROUPS
    }


def sample_population(
    people: list[dict[str, str]],
    *,
    n: int,
    variant: str,
    seed: int = 0,
) -> list[dict[str, str]]:
    """Draw the corpus sample for one occupation.

    R keeps the population's own gender split. K equalises female and male by
    downsampling whichever is larger, which is what makes "any remaining skew is
    the pipeline's" a defensible claim.
    """
    rng = random.Random(f"{seed}:{variant}")
    by_group = {g: [p for p in people if p["gender"] == g] for g in GROUPS}
    for bucket in by_group.values():
        rng.shuffle(bucket)

    if variant == VARIANT_REALISTIC:
        pool = list(people)
        rng.shuffle(pool)
        return pool[:n]

    if variant != VARIANT_BALANCED:
        raise ValueError(f"unknown variant {variant!r}; expected 'R' or 'K'")

    # K: equal female/male halves. `other` is carried at its natural size rather
    # than inflated - there are not enough people to balance it, and pretending
    # otherwise would fabricate precision.
    other = by_group[GENDER_OTHER][: max(1, n // 50)]
    half = (n - len(other)) // 2
    take = min(half, len(by_group["female"]), len(by_group["male"]))
    return by_group["female"][:take] + by_group["male"][:take] + other


def fetch_extracts(
    titles: list[str],
    *,
    batch_size: int = 20,
    quiet: bool = False,
    delay: float = 0.4,
    cache_path: Path | None = None,
    existing: dict[str, str] | None = None,
) -> dict[str, str]:
    """Fetch German Wikipedia lead sections. `exlimit` caps batches at 20.

    Written to survive a long run: the API returns 429 if pushed, so batches are
    spaced out and `Retry-After` is honoured, and progress is checkpointed to
    `cache_path` so an eventual failure costs minutes rather than everything.
    """
    out: dict[str, str] = dict(existing or {})
    client = httpx.Client(headers={"User-Agent": USER_AGENT}, timeout=60.0)

    def checkpoint() -> None:
        if cache_path is not None:
            cache_path.write_text(json.dumps(out))

    try:
        for index, start in enumerate(range(0, len(titles), batch_size)):
            batch = titles[start : start + batch_size]
            for attempt in range(6):
                try:
                    response = client.get(
                        WIKIPEDIA_API,
                        params={
                            "action": "query",
                            "format": "json",
                            "prop": "extracts",
                            # `exintro` is mandatory once exlimit > 1: with any
                            # other extract mode the API silently returns text
                            # for only the first page of the batch. So this is
                            # lead sections, and the length floor is set to
                            # match what German biography leads actually are.
                            "exintro": 1,
                            "explaintext": 1,
                            "exlimit": batch_size,
                            "redirects": 1,
                            "titles": "|".join(batch),
                        },
                    )
                    if response.status_code == 429:
                        wait = float(response.headers.get("Retry-After", 5))
                        time.sleep(min(wait, 60) + attempt * 2)
                        continue
                    response.raise_for_status()
                    pages = response.json().get("query", {}).get("pages", {})
                    for page in pages.values():
                        extract = (page.get("extract") or "").strip()
                        if extract:
                            out[page["title"]] = extract
                    break
                except Exception:
                    if attempt == 5:
                        checkpoint()
                        raise
                    time.sleep(2**attempt)
            time.sleep(delay)
            if index % 20 == 0:
                checkpoint()
                if not quiet:
                    done = min(start + batch_size, len(titles))
                    print(f"  extracts {done}/{len(titles)}", flush=True)
    finally:
        checkpoint()
        client.close()
    return out


def build_documents(
    people: list[dict[str, str]],
    extracts: dict[str, str],
    *,
    variant: str,
    min_chars: int = 120,
) -> list[Document]:
    """Turn labelled people plus their article text into retrievable documents.

    Deduplicated by QID. P106 is multi-valued, so the same person can be sampled
    into several occupations; emitting one document per occupation would give
    them two entries in the index and let them occupy two top-k slots. Instead
    one document carries every occupation it was sampled for.
    """
    merged: dict[str, dict[str, Any]] = {}
    for person in people:
        entry = merged.setdefault(person["qid"], {**person, "occupations": set()})
        entry["occupations"].add(person["occupation"])

    documents: list[Document] = []
    for person in merged.values():
        text = extracts.get(person["title"], "")
        if len(text) < min_chars:
            continue  # a stub gives the retriever almost nothing to match on
        occupations = sorted(person["occupations"])
        documents.append(
            Document(
                doc_id=person["qid"],
                text=text,
                source=f"dewiki:{person['title']}",
                title=person["title"],
                attrs={
                    "gender": person["gender"],
                    # A list, not a scalar: membership is what the study tests.
                    "occupations": occupations,
                    "occupation": occupations[0],
                    "qid": person["qid"],
                    "variant": variant,
                    "n_chars": len(text),
                },
            )
        )
    return documents


# ---- caching --------------------------------------------------------------


def load_or_fetch_populations(
    occupations: list[Occupation], cache_dir: Path, *, quiet: bool = False
) -> dict[str, list[dict[str, str]]]:
    """Populations are stable and slow-ish to fetch; cache them on disk."""
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    populations: dict[str, list[dict[str, str]]] = {}
    for occupation in occupations:
        path = cache_dir / f"population_{occupation.qid}.json"
        if path.exists():
            populations[occupation.label] = json.loads(path.read_text())
        else:
            if not quiet:
                print(f"  querying Wikidata for {occupation.label} ({occupation.qid})")
            people = fetch_population(occupation)
            path.write_text(json.dumps(people))
            populations[occupation.label] = people
        if not quiet:
            rates = base_rates(populations[occupation.label])
            print(
                f"  {occupation.label:12s} n={len(populations[occupation.label]):6d}  "
                + "  ".join(f"{g}={rates[g]:.3f}" for g in GROUPS)
            )
    return populations
