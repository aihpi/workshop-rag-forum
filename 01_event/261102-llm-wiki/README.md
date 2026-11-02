# Meeting 261102: Das KISZ-Wiki

Slides, group questions and starter skills of the RAG Forum on 2 November 2026. The session shows why the KI-Servicezentrum keeps its own team knowledge in an LLM-maintained wiki instead of a RAG system, and how the wiki stays current with little overhead. There is no code to run in this folder.

**Date:** 2026-11-02, 17:30 to 19:00, D-Space, HPI · **Slides:** [llm-wiki_intro.pdf](llm-wiki_intro.pdf) ([.pptx](llm-wiki_intro.pptx))

## In one paragraph

A RAG system embeds every source and searches it at question time; it pays off for large and fast-changing collections but needs development, hosting and maintenance. A hand-written wiki is cheap to run but costs time and goes stale. An LLM wiki sits in between: an LLM reads each source once, writes and links short pages, keeps an index and a log, and people review the pages. A question then meets about 140 condensed pages instead of raw documents, and the model reads the whole index rather than retrieving chunks. The sources stay where they are; each page pins the commit, date or snapshot it was written from.

## Agenda

| Part | Duration |
|---|---|
| Input | 20 min |
| Live demo | 10 min |
| Discussion in groups of three | 15 min |

## Questions for the groups

1. Wenn eine neue Kollegin morgen anfängt: Woher bekommt sie ihr Wissen über eure Abläufe, und wie gut funktioniert das?
2. Wiki oder RAG für euren Fall? Wie viele Dokumente sind es, und wie oft ändern sie sich? Nachschlagen (eine Quelle) oder Verknüpfen (mehrere Quellen)? Was kostet es an Personal, Infrastruktur und Rechenzeit? Wer baut es, wer pflegt es, und wie gut lässt es sich nach dem Start erweitern?
3. Welcher Prozess bei euch könnte auf einem solchen Wissensbestand aufsetzen (Dashboards befüllen, Berichte erstellen, Mails entwerfen)? Was müsste dafür im Wiki oder RAG stehen, und was darf nie ohne menschliche Prüfung laufen?

## Start your own wiki

[skills/](skills/) holds four generic Claude Code skills derived from the KISZ wiki, without anything specific to our team: `wiki-setup` creates the skeleton, `wiki-query` answers questions, `wiki-update` ingests sources and reviews pages, and `wiki-lint` runs a maintenance session. The [skills README](skills/README.md) explains how to install them and what to do first.

## Further reading

- Andrej Karpathy, [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f), the pattern this wiki follows.
- Starmorph, [How to Build Karpathy's LLM Wiki](https://blog.starmorph.com/blog/karpathy-llm-wiki-knowledge-base-guide), 2026-04-09, an overview.

Implementations from the community, as listed on the appendix slide:

| Project | What it is |
|---|---|
| [llmwiki](https://github.com/lucasastorian/llmwiki) | Upload documents, connect Claude through MCP, let it write the wiki |
| [obsidian-wiki](https://github.com/Ar9av/obsidian-wiki) | A framework for AI agents that build Obsidian wikis in Karpathy's pattern |
| [second-brain](https://github.com/NicholasSpisak/second-brain) | A personal knowledge base for Obsidian, maintained by an LLM |
| [llm-wiki-compiler](https://github.com/ussumant/llm-wiki-compiler) | Condenses Markdown files into wikis by topic |
| [CacheZero](https://news.ycombinator.com/item?id=47667723) | The pattern as one npm package |
| [wiki-skills](https://github.com/kfchou/wiki-skills) | Claude Code skills for the pattern |
| [LLM Wiki v2](https://gist.github.com/rohitg00/2067ab416f7bbe447c1977edaaa681e2) | An extended pattern with a memory life cycle and trust scores |

## Files

| Path | Content |
|---|---|
| `llm-wiki_intro.pptx`, `llm-wiki_intro.pdf` | The deck, 16 slides including the appendix |
| `assets/` | Figures, team photos and the QR code to this README used in the deck |
| `skills/` | The starter skills |
