---
name: python
description: >-
  Conventions for Python in this repository: layout under src/api, Flask
  blueprints, typing and style matching neighbors, dependencies in pyproject.toml,
  and verification via Docker/tests instead of host venv. Use when writing or
  refactoring Python in src/api (or other Python services here), editing
  pyproject.toml, or choosing async vs blocking I/O patterns.
---

# Python (this repository)

Stack-specific rules (Weaviate, configs, API docs) live in the **external-knowledge-base** project skill; this skill covers **how to write Python** here.

## Runtime and layout

- **Images use Python 3.10** (e.g. `src/api/Dockerfile`). Prefer syntax and typing that work on 3.10 (`X | Y` unions, `list[str]`, etc.).
- **API code** lives under `src/api/` with **`pyproject.toml`** at `src/api/pyproject.toml`. Shared modules are **`src/api/python_packages/`** (package-per-feature: `retrieval/`, `weaviate/`, `reset/`, …).
- **Imports**: use **relative imports** inside `python_packages` (e.g. `from ..weaviate.weaviate_reset import weaviate_reset_all`), consistent with existing modules.

## Language in code (required)

- **Comments and docstrings**: English only.
- **Log messages** and **API JSON** fields such as `error` / `detail`: English only.
- The **user may prompt in any language**; repository-facing text stays English unless a file is explicitly localized.

## Style and scope

- **Match the surrounding file**: import order, naming, logging (`logger = logging.getLogger(__name__)`), error handling, and typing style.
- **Minimal diffs**: change only what the task requires; no drive-by refactors or unrelated files.
- **New dependencies**: add them only in **`src/api/pyproject.toml`**; the API image installs at build time—do not assume a matching venv on the host.

## Flask routes and async

- Routes may be declared **`async def`**; for **blocking** work (Weaviate client, filesystem, CPU-heavy libs), use **`asyncio.to_thread(...)`** so the event loop is not blocked—follow patterns in `reset/reset.py` and similar handlers.
- Keep blueprint registration and URL patterns consistent with existing blueprints.

## Typing and APIs

- Use **type hints** where neighboring code does (`dict | None`, explicit parameter types when it clarifies public helpers).
- If you change **HTTP request/response shape** or error behavior, update **`documents/API.md`** (see external-knowledge-base skill).

## Tests and verification

- **Do not rely on host `pip` / `python`** for validation unless the user explicitly asks: no ad-hoc `python -c "import …"`, no local venv installs for this stack. Prefer **Docker Compose** / API image rebuild so imports match production.
- Prefer **`test/`** shell scripts and project-provided checks over one-off curls when validating behavior.
- If the user **only tests on a remote server**, follow their workflow; do not insist on local Docker when they have said otherwise.

## When both skills apply

- **external-knowledge-base**: domain (Compose, knowledge YAML, Weaviate, Redis, MCP, `documents/API.md`).
- **python** (this file): generic Python conventions and repo layout for any Python change in this project.
