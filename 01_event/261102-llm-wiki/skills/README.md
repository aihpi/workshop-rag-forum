# Starter skills for your own LLM wiki

Four Claude Code skills to set up, read and maintain a wiki in the pattern of Andrej Karpathy's [LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f): Claude reads each source once, writes short linked Markdown pages from it, and people review those pages. They are a generic version of the skills behind the KISZ wiki presented on 2 November 2026. They contain only skills; the hooks, CI checks and background agents of the KISZ setup are left out, so the skills work in any repository without further setup.

| Skill | What it does |
|---|---|
| [wiki-setup](wiki-setup/SKILL.md) | Interviews you about what the wiki should cover and creates `schema.md`, `index.md`, `log.md`, `sources.md` and page templates |
| [wiki-query](wiki-query/SKILL.md) | Answers a question from the wiki: reads the index, picks the pages, answers with page paths |
| [wiki-update](wiki-update/SKILL.md) | The only skill that writes: ingests a source, files an answer back, reviews a page with its owner, resolves merge conflicts |
| [wiki-lint](wiki-lint/SKILL.md) | Runs a maintenance session: rule checks, contradictions, gaps and redundancy, one finding at a time |

## Install

Copy the four folders into the `.claude/skills/` folder of the repository that will hold your wiki, so that everyone who clones it gets them. To use them in every project instead, copy them into `~/.claude/skills/`.

```bash
git clone https://github.com/aihpi/workshop-rag-forum.git
mkdir -p <your-repo>/.claude/skills
cp -r workshop-rag-forum/01_event/261102-llm-wiki/skills/wiki-* <your-repo>/.claude/skills/
```

Start Claude Code in your repository and ask it to set up a wiki, or type `/wiki-setup`.

## First steps

1. Run `wiki-setup`. It asks at most five questions: what a new colleague should be able to look up, where that knowledge lives today, the language of the pages, who reviews a page and what must never go into the wiki.
2. Ingest one source you know well with `wiki-update`, for example the README of your most important project. Check the pages it writes against what you know.
3. Edit the `description:` of `wiki-query` to list the names of your colleagues, projects, customers and tools. Claude loads a skill when a prompt matches its description, so these nouns decide whether a question reaches the wiki.
4. Ask questions. When an answer is worth keeping, let `wiki-update` file it back.
5. Run `wiki-lint` every few weeks, or after a larger ingest.

## How the skills share rules

Every rule about pages (page types, which changes need a yes, how sources are pinned, open fields, review, privacy) lives in the `schema.md` of your wiki, not in the skills. The skills read it before they act. To change a rule, change `schema.md` with `wiki-setup`.

## Using another model

The skills, the schema and the pages are plain text. Any model or agent that follows written instructions and can read and write files can use them; only the skill loading in step 3 is specific to Claude Code.
