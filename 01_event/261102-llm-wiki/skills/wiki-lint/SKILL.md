---
name: wiki-lint
description: "Runs a maintenance session on the team's LLM wiki (the folder with schema.md and index.md): broken rules, contradictions, gaps, redundant text, missing topics, stale index lines and cross-references, resolved with the user one finding at a time. Use when a user wants to check, clean up or improve the wiki (\"lint the wiki\", \"maintain the wiki\", \"clean up the wiki\", \"what is missing in the wiki\", \"what can be condensed\", \"Wiki aufräumen\", \"Wiki pflegen\", \"Widersprüche im Wiki\")."
---

# wiki-lint

## Purpose

One maintenance session per run: the checks, the findings ranked, then the findings resolved with the user one at a time. Done when every finding has a status (`fixed`, `deferred`, `rejected` with the reason, or `open` for the next run) and every fix went through Apply of `wiki-update`.

## Authority

- Alone: read-only checks and the findings file.
- Propose: every page change, including condensing, merging, new topics, index lines, cross-references and answers to open fields.
- Never: write a page without the user's yes for that finding; delete a page without an explicit yes; change `schema.md` or the templates in passing (that is a separate change through `wiki-setup`); stash, reset, switch or push in the user's repository.
- Budget: ten resolved findings per session.

## State

- Persists: `${WIKI_LINT_DIR:-~/.wiki-lint}/<YYYY-MM-DD>-findings.md`, one row per finding with ID, check, `file:line`, evidence, proposed fix and status. It lives outside the wiki, so that unfinished findings never reach the pages.
- Forgotten: drafted page text the user did not confirm.

## Rules

- No evidence, no finding. Every finding cites `file:line` and quotes the text or the command output.
- One finding per question, with your recommended fix and its evidence.
- The recommendation follows the source precedence of `schema.md`. When it does not decide, recommend asking the page owner (`TBD (ask <owner>, <ISO date>)`) and take no side.
- Condensing keeps one home per fact: the most specific page keeps the text, the others link to it.
- Privacy findings rank first and are removed, not discussed.
- If the team has a writing-style guide or skill, follow it for every drafted fix.

## Steps

1. **Setup.** Find the wiki root as `wiki-query` describes and read `schema.md`. If the wiki is in git, the working tree must be clean and current; otherwise stop, name the branch and the changed files, and let the user decide.
2. **Earlier run.** If a findings file with `open` rows exists, re-check those rows against the current pages, mark what has been fixed since, and continue with the rest. Scan anew only when none is open.
3. **Checks.** Run the rule checks, then the judgment checks in [references/checks.md](references/checks.md).
4. **Rank.** Write the findings file in this order: privacy, contradictions, wrong or overdue facts, rule violations, gaps, redundancy, structure, findability.
5. **First message.** The number of findings per check, then the first question.
6. **Per answer.** Yes: draft the change, show it, and hand it to Apply of `wiki-update` with `<op>` = `lint`. No: `rejected` with the reason. Later: `deferred`. Update the findings file after every answer.
7. **End.** At the budget or when the user stops, list what stays open and where the findings file is.
