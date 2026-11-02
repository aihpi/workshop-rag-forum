---
name: wiki-setup
description: "Sets up a new LLM wiki: a folder of Markdown pages that Claude writes from sources and people review. Creates schema.md, index.md, log.md, sources.md and page templates after a short interview about what the wiki should cover. Use when a user says \"set up a wiki\", \"start an LLM wiki\", \"create a knowledge base for our team\", \"Wiki anlegen\", \"Wissensbasis aufsetzen\", or wants to adapt the wiki's page types and rules later."
---

# wiki-setup

## Purpose

One run creates the skeleton of an LLM wiki, or changes the schema of an existing one. The wiki follows the pattern of Andrej Karpathy's "LLM Wiki": sources stay where they are, Claude reads each source once and writes short, linked pages from it, and people review those pages. The other skills (`wiki-query`, `wiki-update`, `wiki-lint`) read the `schema.md` this skill writes, so every rule lives in one file.

The run is done when the wiki folder holds `schema.md`, `index.md`, `log.md`, `sources.md`, a `_template.md` in every page folder and `topics/_template.md`, and the user has confirmed the schema.

## Rules

- Ask before writing. Show the planned folders, page types and source table in one message and write only after a yes.
- Keep the schema short. A rule the team will not follow is worse than no rule. Start with the defaults in [references/schema-template.md](references/schema-template.md) and change only what the user asks for.
- One rule lives in one place. Templates and skills point to `schema.md` instead of restating it.
- Never put personal contact data, participant lists or assessments of people into the wiki, its examples or its templates.

## Steps

1. **Location.** Ask where the wiki lives. Recommend `wiki/` at the root of a git repository the team already shares, so that every change is a commit and can be reviewed. If the folder already has a `schema.md`, switch to changing the schema (step 6).
2. **Interview.** Ask at most five questions, one at a time, each with a recommended answer:
   1. What should a new colleague be able to look up? This gives the page types, for example projects, people, how-tos, events, customers, systems.
   2. Where does the knowledge live today? This gives the source table, for example a Git host, a ticket system, a shared drive, a website, interviews.
   3. In which language are pages written?
   4. Who reviews a page? Usually the person a page describes or the person responsible for the project.
   5. What must never go into the wiki? Start from the privacy defaults of the template and add what the user names.
3. **Plan.** Fill in [references/schema-template.md](references/schema-template.md) with the answers: one row per page type with its folder and frontmatter keys, one row per recurring source. Show the plan.
4. **Write.** After the yes, create:
   - `schema.md` from the filled template.
   - `index.md`, `log.md` and `sources.md` from [templates/](templates/).
   - One folder per page type with a `_template.md`, adapted from [templates/_template-entity.md](templates/_template-entity.md).
   - `topics/_template.md` from [templates/_template-topic.md](templates/_template-topic.md).
5. **Log.** Append the first entry to `log.md`: `## [<today>] setup | chat | schema.md, index.md, log.md, sources.md` with one line on what the wiki covers.
6. **Changing the schema later.** Show the change as a diff of `schema.md` and the affected templates, apply it after a yes, and add a `log.md` entry with `<op>` = `schema`. Existing pages are migrated by `wiki-lint`, not in this run.

## Report

The folder that was created, the page types and sources it knows, and the next step: ingest the first source with `wiki-update`, for example the README of the most important project or a how-to the team uses every week.
