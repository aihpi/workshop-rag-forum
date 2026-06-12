# workshop-rag-forum

A forum for monthly meetings centred around **Retrieval-Augmented Generation (RAG)**.
Each meeting explores a different topic (embedding models, vector compression,
retrieval strategies, evaluation, etc.).

## Meeting workflow

Each meeting is prepared on its own branch and merged once it is ready:

1. **Branch** — create `feature/YYMMDD-description` (e.g. `feature/250615-turbovec`).
2. **Materials** — live under `03_workshop/YYMMDD-topic/` with a dedicated `README.md`
   that explains the experiment / demo in detail.
3. **Virtual environment** — each meeting gets its own venv in the repo root,
   named `.venv_YYMMDD-topic` (e.g. `.venv_250615-turbovec`), so meetings stay isolated.
4. **Merge** — once the meeting is prepared, the branch is merged into `main`.

Dependencies are managed exclusively with **uv** (`uv add <pkg>`, never `pip install`).
To target a meeting's venv when adding/syncing dependencies:

```bash
uv venv .venv_250615-turbovec --python 3.12
UV_PROJECT_ENVIRONMENT=.venv_250615-turbovec uv add <packages>
UV_PROJECT_ENVIRONMENT=.venv_250615-turbovec uv run python 03_workshop/250615-turbovec/01_download_data.py
```

## Repository layout

```
03_workshop/              # one folder per meeting: YYMMDD-topic/
  250615-turbovec/        # first meeting (see its README)
data/                     # downloaded corpora & generated vectors (gitignored)
src/workshop_rag_forum/   # shared package code (from the template)
notebooks/ docs/ reports/ references/ tests/
.env_example              # copy to .env and fill in your endpoint + key
```

## Meetings

| Date     | Topic     | Folder                          | Summary                                              |
|----------|-----------|---------------------------------|------------------------------------------------------|
| 25-06-15 | turbovec  | `03_workshop/250615-turbovec/`  | Illustrating turbovec vector compression vs. a float32 embedding baseline |

## Setup

See [installation.md](installation.md) for installing uv and Python, and
[development.md](development.md) for development workflows. Copy `.env_example` to
`.env` and fill in your embedding endpoint and API key before running a meeting's scripts.

## About

Built by the **KI-Servicezentrum / AI@HPI** team using the
[aihpi/template-ai-project](https://github.com/aihpi/template-ai-project) template.
