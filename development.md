# Development

## Setting Up uv

This project is set up to use [uv](https://docs.astral.sh/uv/) to manage Python and
dependencies. First, be sure you
[have uv installed](https://docs.astral.sh/uv/getting-started/installation/).

Then [fork the aihpi/workshop-rag-forum
repo](https://github.com/aihpi/workshop-rag-forum/fork) (having your own
fork will make it easier to contribute) and
[clone it](https://docs.github.com/en/repositories/creating-and-managing-repositories/cloning-a-repository).

## Basic Developer Workflows

The `Makefile` simply offers shortcuts to `uv` commands for developer convenience.
(For clarity, GitHub Actions don't use the Makefile and just call `uv` directly.)

```shell
# First, install all dependencies and set up your virtual environment.
# This simply runs `uv sync --all-packages --all-extras` to install the dev
# tools and every meeting in the workspace (see "Repository layout" below).
make install

# Run uv sync, lint, and test:
make

# Linting:
make lint

# Run tests:
make test

# Delete caches and the virtual environment:
make clean

# Upgrade dependencies to compatible versions:
make upgrade

# To run tests by hand:
uv run pytest   # all tests
uv run pytest -s 01_event/260901-rag-bias/tests/test_store.py  # one file, showing outputs

# Dependency management directly with uv. The root holds no code, so a
# runtime dependency belongs to a meeting:
uv add --package rag-bias package_name
# Add a development dependency (root, shared by every meeting):
uv add --dev package_name
# Update to latest compatible versions (including dependencies on git repos):
uv sync --upgrade
# Update a specific package:
uv lock --upgrade-package package_name
# Update dependencies on a package:
uv add --package rag-bias package_name@latest

# Run a shell within the Python environment (after make install):
source .venv/bin/activate
```

See [uv docs](https://docs.astral.sh/uv/) for details.

## Repository layout

One folder per meeting in `01_event/YYMMDD-topic/`, and nothing else. A meeting folder holds documentation, figures, driver scripts and, where a meeting needs code of its own, its packages. A README covers how to run it and what comes out; where the method needs arguing, a METHOD.md covers why, and where the code needs explaining, an ARCHITECTURE.md. The root holds only what every meeting shares: tooling, `.env` and `data/`.

The repository is a [uv workspace](https://docs.astral.sh/uv/concepts/projects/workspaces/). The root `pyproject.toml` holds no package (`tool.uv.package = false`), only the member list, the dev tools and the ruff/basedpyright/pytest settings. Every meeting with code is a member with its own `pyproject.toml`, so its dependencies never leak into another meeting. One `uv.lock` and one `.venv` cover all of them: `uv sync --all-packages --all-extras`, which is what `make install` and CI run.

| Member | Folder | Kind |
|---|---|---|
| `turbovec-demo` | `01_event/260615-turbovec/` | standalone scripts, not a package (`tool.uv.package = false`) |
| `rag-bias` | `01_event/260901-rag-bias/` | packages `workshop_rag_forum` and `rag_bias` in its `src/`, with tests and the `rag-bias` command; see its [ARCHITECTURE.md](01_event/260901-rag-bias/ARCHITECTURE.md) |

A meeting without code, such as `261102-llm-wiki`, has no `pyproject.toml` and is not a member.

## Adding a meeting

Create `01_event/YYMMDD-topic/`. A meeting without code needs nothing else. A meeting with scripts adds a `pyproject.toml` with its own dependencies and `tool.uv.package = false` (see `260615-turbovec`). A meeting with importable code adds a package under its own `src/`, tests, and a `pyproject.toml` with a hatchling build (see `260901-rag-bias`); add its `tests` to `testpaths`, and its `src` and `tests` to `[tool.basedpyright]` in the root `pyproject.toml` and to `SRC_PATHS` in `devtools/lint.py`. Either way, list the folder under `[tool.uv.workspace] members` and its `src` under `[tool.ruff] src`. Test file names must stay unique across meetings, because pytest imports them by basename.

`make lint` runs codespell, `ruff check --fix`, `ruff format` and basedpyright over `devtools` and the `src` and `tests` of every meeting package, reformatting in place; codespell also rewrites the root `README.md`. Driver scripts and the meeting READMEs are deliberately out of scope. basedpyright runs clean, zero errors and zero warnings. The three `reportUnknown*` rules are disabled in `pyproject.toml` because they fire only on values flowing out of numpy/pandas/pytest stubs; every rule that checks our own annotations stays on.

## IDE setup

If you use VSCode or a fork like Cursor or Windsurf, you can install the following
extensions:

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python)

- [Based Pyright](https://marketplace.visualstudio.com/items?itemName=detachhead.basedpyright)
  for type checking. Note that this extension works with non-Microsoft VSCode forks like
  Cursor.

## Documentation

- [uv docs](https://docs.astral.sh/uv/)

- [basedpyright docs](https://docs.basedpyright.com/latest/)

