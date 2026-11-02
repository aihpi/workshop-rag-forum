# Checks

Two kinds. The rule checks compare pages against `schema.md` and need no judgment; run them with `grep` and by reading frontmatter. The judgment checks need reading. Report each finding with `file:line`, the quoted text and one proposed fix.

## Rule checks

| Check | How to find it | Fix |
|---|---|---|
| Index incomplete or stale | Compare the page files (without `_template*.md`) with the links in `index.md`; compare each line's summary with the page's `summary:` | Rewrite the line, add the missing one, remove the one without a page |
| Summary missing or too long | A page without `summary:`, or one longer than 20 words | A summary that says what the page answers |
| Frontmatter key missing | Keys of the page type in `schema.md` that the page lacks | The value from a source, or a `TBD` |
| Source missing | An entity or topic page without `sources:`, or with an unpinned pointer (no commit, date or path) | The pinned pointer, or a question to the page owner |
| Open field in the wrong form | `grep -rn "TBD" .` and keep the hits that do not read `TBD (ask <full name>, <date or one-off event>)` | The full form |
| Open field overdue | A `TBD` whose date has passed or whose event has happened | The value from a source, or a reminder to the person named |
| Broken link | A relative link to a file that does not exist | The correct path, or remove the link |
| Review out of date | A page whose last commit (`git log -1 --format=%cs -- <page>`) is newer than its `reviewed:` date | Offer Review in `wiki-update` with the page owner |
| Log edited | `git log -p -- log.md` shows a removed or changed line | Restore the line; corrections go into a new entry |
| Privacy | E-mail addresses and phone numbers of individuals, and anything else the schema excludes | Remove it |

## Judgment checks

1. **Contradictions.** A fact that differs between two pages (a status, a date, a name, a number), or between an entity page and a topic page. Fix: the value from the source that wins by precedence, and the contradiction recorded under the topic's "Contradictions and open questions" with both sources.
2. **Orphans.** A page that no other page links to, apart from `index.md`. Fix: a link from the pages it belongs to.
3. **One-way links.** A Related section that links in one direction only. Fix: the back-link.
4. **Unlinked mentions.** A page that names another page's subject in prose without linking it. Fix: the link.
5. **Missing topics.** A theme named on two or more entity pages without a `topics/` page. Fix: a topic page derived from those entities.
6. **Thin topics.** A topic page that no entity lists, or one built on a single entity. Fix: link it from the entities, or fold it into the entity page.
7. **Missing pages.** Something named on two or more pages without a page of its own, or a term used on several pages without a definition. Fix: a page from the folder's template, or a definition on the page that owns the concept.
8. **Redundancy.** The same fact or paragraph on three or more pages, pasted source text longer than the page's own summary, or two pages about the same thing. Fix: one home per fact with links from the others, a short summary with the pinned source, or one merged page.
9. **Findability.** An index line that does not say what the page answers, or a page that an everyday word cannot find. Fix: a better `summary:` or a new entry in `aliases:`.
10. **Unverified claims.** A page where many sentences carry `(inferred)` or `(unverified)`. Fix: the source to read, then Ingest.
