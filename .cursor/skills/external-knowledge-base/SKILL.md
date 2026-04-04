---
name: external-knowledge-base
description: >-
  Guides work on the docker-External-Knowledge-Base stack: Docker Compose API,
  Python packages under src/api, knowledge base YAML configs, Weaviate retrieval,
  SearXNG/Mercury/Redis integrations, and MCP tools. Use when editing this
  repository, HTTP routes, retrieval logic, configs, tests, or deployment docs.
---

# External Knowledge Base (project)

## Language policy (required)

- **Code comments and docstrings**: English only.
- **User-facing strings** returned by the API (JSON `error`, `detail`, and similar), **log messages**, and **inline help in scripts**: English only.
- The **user may write prompts in any language**; still keep repository-facing text (code, docs meant for developers) in English unless a file is explicitly localized.

## Stack (mental model)

- **Orchestration**: Docker Compose (`docker-compose.yml`); API typically exposed on host port `8080`.
- **HTTP API**: Python service under `src/api/`; route handlers and shared logic live in `src/api/python_packages/` (e.g. `retrieval/`, `scrape/`, `weaviate/`, `knowledge_base_config/`).
- **Knowledge bases**: YAML under `knowledge_base/configs/` (see `example.yml`); `knowledge_id` maps to config stem and optional `!section` for spreadsheets (`parse_knowledge_id`).
- **Retrieval**: Chunk vs file mode; Weaviate when `USE_MOCK_DB` is false; mock path for local testing when true.
- **Docs**: HTTP endpoints in [documents/API.md](../../../documents/API.md); layout in [documents/STRUCTURE.md](../../../documents/STRUCTURE.md); [README.md](../../../README.md) covers rclone mount and MCP Docker test scripts.

## Editing conventions

- **Match neighboring code**: imports, typing, error handling, and naming as in the same package.
- **Scope**: Change only what the task needs; avoid unrelated refactors.
- **API contract changes**: Update [documents/API.md](../../../documents/API.md) (request/response fields, examples, error behavior).
- **Blocked scrape paths**: Extensions live in `src/api/python_packages/scrape/non_web_page_extensions.py` (`NON_WEB_PAGE_EXTENSIONS`, lowercase, no leading dot).

## Tests and verification

- Shell tests under `test/` (e.g. retrieval, MCP profile `mcp-test`). Prefer the project’s existing scripts over ad-hoc curls when validating behavior.
- If the user validates on a **remote server** only (no local Docker), follow their remote-testing workflow when applicable.

## MCP

- MCP tools mirror HTTP behavior (`search_web`, `search_news`, `scrape_web_page`, `search_<knowledge_id>_chunks` / `_files`). Bearer auth uses the same API key expectations as documented in README/API.
