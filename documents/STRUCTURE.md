# Repository structure

High-level map of **docker-External-Knowledge-Base**: a Docker Compose stack with an HTTP API (search, scrape, news, knowledge retrieval), supporting services (Redis, Weaviate, SearXNG, Mercury, embeddings), and an MCP server.

## Top level

| Path | Role |
|------|------|
| `docker-compose.yml` | Service definitions, networks, volumes, profiles (e.g. `mcp-test`). |
| `.env` / `.env.example` | Runtime secrets and tunables (`API_KEY`, timeouts, URLs). |
| `startup.sh` | Optional host bootstrap helper. |
| `README.md` | rclone / Google Drive mount notes and MCP Docker test entry points. |
| `documents/API.md` | HTTP API usage (`/search`, `/scrape`, `/news`, `/retrieval`). |
| `documents/STRUCTURE.md` | This file (repository layout). |

## `src/` — application code and service configs

| Path | Role |
|------|------|
| `src/api/` | Main API container: Dockerfile, `pyproject.toml`, app entry, `static/`, `templates/`. |
| `src/api/python_packages/` | Feature packages imported by the API (see below). |
| `src/mcp_server/` | MCP server image: tools that call the API (`search_web`, `search_news`, etc.). |
| `src/mcp_test/` | Image and runner used by Compose profile **`mcp-test`** for one-shot MCP smoke tests. |
| `src/nginx/` | Reverse proxy config (`nginx.conf`); publishes host **`8080`** → API stack. |
| `src/searxng/` | SearXNG settings mounted into the SearXNG container. |
| `src/weaviate/` | Weaviate service image build context (`Dockerfile`); behavior wired in Compose. |

## `src/api/python_packages/` — API modules

Packages are grouped by concern. Names reflect typical responsibilities (exact entrypoints live under each package).

| Package | Typical responsibility |
|---------|-------------------------|
| `auth/` | API authentication (e.g. Bearer token). |
| `search/` | `POST /search` → SearXNG + optional Mercury full text. |
| `scrape/` | `POST /scrape` → Mercury; `non_web_page_extensions.py` for blocked path suffixes. |
| `news/` | `POST /news` → Google News RSS + optional Mercury. |
| `google_news_url/` | Resolving redirect URLs for news items. |
| `retrieval/` | `POST /retrieval` → chunk/file semantic search; mock vs Weaviate paths. |
| `weaviate/` | Weaviate query helpers used by retrieval. |
| `knowledge_base_config/` | Loading YAML from `knowledge_base/configs/`, `knowledge_id` / section parsing. |
| `embedding/` | Embedding client and embedding-service readiness helpers. |
| `ingest/` / `index/` / `update/` | Ingestion and indexing pipelines toward the vector store. |
| `upload_file/` / `file_host/` | File upload and serving helpers where used by routes. |
| `image_describe/` | Image description integration if exposed by the API. |

## `knowledge_base/` — data and config

| Path | Role |
|------|------|
| `knowledge_base/configs/` | One YAML per knowledge base (e.g. `example.yml`); `knowledge_id` is the stem without `.yml`. Optional `knowledge_id!SheetName` for spreadsheet sections. |
| `knowledge_base/files/` | Local knowledge files and mount points used by ingestion (layout depends on your config). |

The API container mounts `./knowledge_base` at `/app/knowledge_base` (see `docker-compose.yml`). The MCP server mounts `./knowledge_base/configs` read-only for config discovery.

## `test/` — shell-based checks

Integration-style scripts from the repo root (search, news, knowledge retrieval, MCP-in-Docker). Shared MCP Docker logic: `test/mcp-test-docker-common.sh`.

## `cache/`

Local cache for Text Embeddings Inference (TEI) model weights under `cache/tei/` (large; usually gitignored or machine-local).

## `documents/`

Primary reference docs for contributors: **`API.md`** (HTTP endpoints) and **`STRUCTURE.md`** (this file). Other notes (e.g. rclone, Dify) may live alongside them; none of this is required at API runtime.

## Cursor project skill

Agent guidance for this repo (language policy, stack hints): `.cursor/skills/external-knowledge-base/SKILL.md`.
