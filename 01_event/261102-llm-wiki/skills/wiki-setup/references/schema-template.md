# Schema of <wiki name>

The rules for writing and checking pages of this wiki. The skill `wiki-query` tells a reader how to answer a question; this file tells a writer (`wiki-update`, `wiki-lint`) what a page must look like. One rule lives here and nowhere else.

## Layers

The wiki has three layers. Sources are read, never modified; they are registered in `sources.md`. Pages are written by Claude from those sources and reviewed by people. The schema is this file.

## Page types and folders

| Type | Folder and file | Frontmatter keys | Tier |
|---|---|---|---|
| <Entity, for example Project> | `<folder>/<slug>.md`, from `<folder>/_template.md` | title, summary, people, status, sources, topics, aliases | Confirm; new page Free |
| <Entity, for example Person> | `people/<first-last>.md` | name, summary, sources | Confirm; some sections only on the person's own word |
| <Entity, for example How-to> | `how-to/<slug>.md` | title, summary, sources, aliases | Confirm; new page Free |
| Topic | `topics/<slug>.md`, from `topics/_template.md` | title, summary, entities, updated, sources | Free |
| Source registry | `sources.md` | none | Confirm |
| Catalog | `index.md` | none | Free; rewritten after every change |
| Timeline | `log.md` | none | Append only; an entry is never edited |
| Schema | `schema.md`, `_template.md` files | none | Confirm |

Slugs are short, lowercase and hyphenated. Pages about dated occasions start with the date: `YYYY-MM-DD-<slug>`.

## Tiers

Free means Claude writes without asking: a new entity page created from a source, topic pages, `index.md` and the `log.md` entry. Confirm means Claude shows the change and applies it after the user says yes: every change to an existing page, every change to a person page, a new row in `sources.md`, a schema change. Sections that describe how a person likes to work or to be addressed change only on that person's own word.

## Provenance

Every entity and topic page lists its sources in the frontmatter as pinned pointers, one per line, so that a reader can open the exact version a fact came from:

```
sources:
  - https://github.com/<org>/<repo>@<commit>
  - https://example.org/page (retrieved <YYYY-MM-DD>)
  - <shared drive path to a document> (<YYYY-MM-DD>)
  - interview <full name> <YYYY-MM-DD>
```

A repository is pinned by its commit, a web page by the retrieval date, a document by its path and date, an interview by name and date. A single claim without a source carries `(inferred)` or `(unverified)` inline.

Source precedence when two sources disagree: <for example: final report > repository > interview > any wiki page>. Within one rank a newer source wins over an older one. A changed fact replaces the old value; git history keeps the old one, and the `log.md` entry names the changed fact.

## Summaries and aliases

Every page except `index.md`, `log.md` and `sources.md` has a one-line `summary:` of at most 20 words that says what the page answers. Pages that people search for under other names carry `aliases:` with the everyday words, abbreviations and former names they use, in every language the team speaks. `index.md` repeats both, so the first read finds the page.

## Open fields

An unknown value is written `TBD (ask <full name>, <ISO date or one-off event>)`, for example `TBD (ask Jane Doe, after the kick-off)`. A bare `TBD` and recurring triggers such as "next weekly" are not allowed, because they never resolve. A field that is empty on purpose takes `n/a`. When a skill touches a page with open fields, it asks at most five questions per session; the rest stay open.

## Review

A page is reviewed when the person it concerns confirms it. The skill `wiki-update` (Review) writes two fields:

```
reviewed: <YYYY-MM-DD>
reviewed_by: <full name>
```

A page whose last commit is newer than `reviewed` has changed since its review. Pages are reviewed when they are created or changed, not in a campaign.

## Index

`index.md` is the catalog: one section per page type, one line per page, in this form:

```
- [Title](path): summary (date · N sources · reviewed|changed|unreviewed) Also: aliases.
```

`wiki-update` rewrites the lines of every page it touched; `wiki-lint` checks that the index lists every page and nothing else. Templates are not listed.

## Log

`log.md` is append only. Each change adds one entry, `## [YYYY-MM-DD] <op> | <source> | <pages>`, where `<op>` is `setup`, `schema`, `ingest`, `file-answer`, `review`, `lint` or `edit`, and `<source>` is a name from `sources.md`, `chat` or `interview <name> <date>`. One to three lines below the heading say what changed.

## Privacy

The wiki holds only what the whole team may know. It never holds e-mail addresses or phone numbers of individuals, participant or customer lists, assessments of colleagues, or <anything else the team names>. Functional mailboxes are allowed. Names of external contact persons are allowed without address or number.
