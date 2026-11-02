---
name: wiki-update
description: "Writes to the team's LLM wiki (the folder with schema.md and index.md) and is the only skill that does. Ingests a source (a link, a document, a repository, a pasted text, an interview), files a chat answer back, reviews a page with its owner, or resolves a merge conflict in the wiki. Use when a user says \"add this to the wiki\", \"ingest\", \"update the knowledge base\", \"file this answer\", \"review this page\", \"is this still right\", \"ins Wiki\", \"Wiki aktualisieren\", \"stimmt das noch\", corrects a fact the wiki holds, or pastes a link and wants it recorded."
---

# wiki-update

The wiki's `schema.md` holds the rules: page types, tiers, `sources:` pointers, open fields, review, index, log and privacy. This skill holds the operations on the wiki. Every operation ends in Apply, the one write path, and every run ends with the Report.

## Purpose

One run does one operation. It is done when its criterion holds.

| Operation | Done when |
|---|---|
| Ingest | the user confirmed the plan, each page on it is written or declined, and Apply is done |
| File answer | the synthesis is on its topic page with the source page of every claim, and Apply is done |
| Review | the named person said yes and `reviewed` and `reviewed_by` are written; on a no, nothing is stamped |
| Conflicts | no conflict marker is left in the wiki, the index is complete, and the merge or rebase continued |

## Authority

- Alone: read `schema.md`, `index.md`, the pages and the sources; after the plan is confirmed, write the pages the schema puts in the Free tier; in Apply, rewrite the index lines and append the `log.md` entry.
- Propose: the plan of pages, with one yes before anything is written; every change to an existing page; every change to a person page; a new row in `sources.md`; filing a chat answer; a review stamp, which the named person confirms.
- Never: write `reviewed` or `reviewed_by` outside Review; change how a person likes to work or to be addressed except on that person's own word; edit or drop an existing `log.md` entry; push or merge on the user's behalf.
- Budget: five open-field questions per session.

## Rules

- Read `schema.md` before any operation. A rule lives there and nowhere else.
- If the team has a writing-style guide or skill, follow it for every page.
- No source, no claim. A page without pinned `sources:` does not leave Apply, every claim of a filed answer names its source page, and every line added to a topic names the page it comes from.
- Condense, do not paste. A page sums up a source in its own words; a long pasted text becomes two or three sentences and the pinned source.
- Open fields follow the schema: `TBD (ask <full name>, <ISO date or one-off event>)`, or `n/a` when empty on purpose. Never guess a value.
- Privacy follows the schema. Never copy e-mail addresses or phone numbers of individuals, participant lists or assessments of people from a source. Remove anything of that kind before Apply.
- Contradictions follow the source precedence of the schema. When it does not decide, take no side: show both sources and recommend a `TBD` for the page owner.

## Steps

### Setup

Find the wiki root as `wiki-query` describes. If the wiki is in a git repository, check that the working tree has no uncommitted changes outside the files this run will write, and pull the current state. If the tree is dirty or behind, stop before the first write, name the branch and the changed files, and let the user decide; never stash, reset or switch for them.

### Ingest

1. **Source.** Find the source in `sources.md`. If it is not there, propose a row and ask whether to add it.
2. **Read.** Read the source once: a web page with a fetch tool, a local file directly, a repository through its README, its main configuration files and its recent history, a pasted text as it is. Note the pinned pointer (commit, retrieval date, path and date, or interview name and date). A source that cannot be read, such as a page behind a login, is reported; nothing is written from it and nothing is invented.
3. **Plan.** Read `index.md`. List the pages the source touches: the page it is about (existing or new, by slug), pages it mentions, topic pages and person pages. Show the list in one message with what changes on each, and ask once whether to proceed. If `log.md` already names the same source, plan only what differs from the pages as they are.
4. **Write.** New pages start from the folder's `_template.md` and get a `sources:` list with the pinned pointer. Changes to an existing page and to a person page are shown as a diff and applied after a yes.
5. **Open fields.** For each field the source does not answer, ask the user, one question at a time with your recommended answer, at most five per session. The rest stay `TBD`.
6. **Topics.** For every theme the new content shares with at least one other page, create or update `topics/<slug>.md` from `topics/_template.md`. Derive it from the entity pages named in its `sources:`, never from its own previous text: link both entities, add one line to "What we learned" with the page it comes from, and record contradictions. Do not create a topic for a theme only one page mentions.
7. **Apply** with `<op>` = `ingest` and `<source>` = the source as named in `sources.md`.

### File answer

When a chat answer is worth keeping and the user says yes, choose the topic page it belongs to, or create `topics/<slug>.md`, and add the synthesis with the source page of every claim. Apply with `<op>` = `file-answer` and `<source>` = `chat`.

### Review

The owner of a page is the first name in `people:`, the person the page describes, or whoever the user names. Show what changed since the last review (`git log -p --since=<reviewed> -- <page>`), or the whole page when it has no stamp, and ask the owner whether the page is right. On a yes, write `reviewed: <today>` and `reviewed_by: <full name>`. On a no, take the corrections through Ingest step 4 first, then ask again. Apply with `<op>` = `review`.

### Apply

The one write path for every operation.

1. Check the tiers of the schema for every file: a change to an existing page or a person page needs the yes from this session; without one, ask now.
2. Check provenance: every new or changed page has its `sources:` pinned.
3. Check privacy: search the changed files for e-mail addresses, phone numbers and anything else the schema excludes, and remove what you find.
4. Rewrite the `index.md` line of every new or changed page in the form the schema gives, under the right section, and remove lines of deleted pages.
5. Append one entry to `log.md`: `## [YYYY-MM-DD] <op> | <source> | <pages>` and one to three lines on what changed, naming a changed fact when a value was replaced.
6. If the wiki is in git, propose one commit for the change with a message that says why. Commit after a yes; pushing and opening a merge request stay with the user.

### Conflicts

A merge or rebase can conflict in `log.md`, where every operation appends, and in pages two people edited.

1. Take one conflicted file and one hunk at a time.
2. Show both sides in a short block and say what each side wants.
3. Propose fixes with your recommendation first: keep both `log.md` entries in date order (never drop one), take the newer source for a fact and record the older one under the topic's contradictions, or merge two summaries into one line.
4. Apply the fix the user chooses and move to the next hunk.
5. After the last hunk, rebuild the affected `index.md` lines, then `git add` the files and let the user continue the merge or rebase.

### Report

Pages created, pages changed, review stamps set, open `TBD`s with whom to ask, changed person pages, the commit if one was made, and what stayed open because a confirmation was declined or not given.
