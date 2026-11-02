---
name: wiki-query
description: "Answers questions from the team's LLM wiki (the folder with schema.md and index.md): projects, people, workflows, events and topics. Load first whenever a question names something the team knows about: a colleague, a project, a customer, a recurring workflow, an event or a tool. A question without a writing verb is a lookup (who, when, where, which link, who is responsible, what did we do on X): read index.md and answer with page paths. Edit this description to list your own nouns, because that is what makes the skill trigger."
---

# wiki-query

This skill reads an LLM wiki: Markdown pages that Claude wrote from sources and people reviewed. Read `index.md` first; it lists every page with a one-line summary. Then read only the pages the question needs; they are short. The rules for writing pages are in `schema.md`; a reader does not need them.

## Finding the wiki

The wiki root is the folder that holds `schema.md` and `index.md`: `$WIKI_DIR` when set, otherwise `wiki/` in the current repository, otherwise the current directory when it holds both files. If none of these exists, ask the user for the path.

## Answering a question

1. Read `index.md` and pick the pages whose summary or aliases match. For a question that spans several projects or events, start with `topics/`.
2. Read those pages in full. Follow a link under Related only when the answer needs it.
3. Answer with the file path of every page a claim comes from.
4. Say how far the answer can be trusted when it matters: a page with `reviewed:` and `reviewed_by:` was confirmed by a person; a page without them is a draft nobody has confirmed yet; a `TBD (ask <name>, <when>)` is an open field, and the answer names whom to ask.
5. If the answer is a synthesis worth keeping (a comparison, a lesson across projects, a connection nobody wrote down), offer once to file it back with `wiki-update`. Do not file it without a yes.

## Where to look

| Question | Read |
|---|---|
| Everything at a glance | `index.md` |
| What changed recently | `grep "^## \[" log.md \| tail -10` |
| Where a fact comes from | the page's `sources:` field, then `sources.md` |
| A theme across several pages | `topics/<slug>.md` |
| The rules for writing pages | `schema.md` |

## Rules

- Answer from the pages, not from memory. When the wiki does not answer the question, say so and name the source in `sources.md` that probably does.
- Do not read raw sources at question time when a page covers the question. The pages exist so that each source is read once.
- Never repeat personal contact data, participant data or assessments of people, even if a page should contain them; report the page to the user instead.
- Do not change pages. Every change goes through `wiki-update`.
