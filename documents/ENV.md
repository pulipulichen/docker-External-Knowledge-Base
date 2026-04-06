# Environment variables (`.env` and `.env.example`)

The repo-root **`.env`** file is copied from [`.env.example`](../.env.example). Docker Compose uses it for **container environment variables** and for **`${VAR}` substitution** in `docker-compose.yml`.

## Quick start

1. From the repo root: `cp .env.example .env`
2. Replace placeholders (e.g. `YOUR_API_KEY`, `YOUR_GEMINI_API_KEY`) with real secrets and URLs.
3. Run `docker compose up`. Services such as `api`, `markdown_converter`, `weaviate`, and `weaviate_ui` load variables via `env_file: .env` (see [`docker-compose.yml`](../docker-compose.yml)).

### Section headers like `[api]`

`.env.example` uses INI-style **`[api]`**, **`[redis]`**, and similar lines only as **visual grouping**. Docker Compose `env_file` parsing accepts **`KEY=VALUE`** lines and **`#` comments**. Section-header lines are usually ignored; if your Compose version errors on unparsed lines, delete the `[…]` lines—the variables themselves are unchanged.

### SearXNG

The `searxng` service does **not** mount the full `.env` file (to avoid feeding INI-style content as raw env). `SEARXNG_SECRET` is injected only through compose **`${SEARXNG_SECRET:-…}`** substitution from the project-root `.env`, as noted in `docker-compose.yml`.

### TEI and Hugging Face

The `tei` service expects **`HF_TOKEN`** (see `docker-compose.yml`), which is not listed in `.env.example`. Add it to `.env` when you need private models or higher quotas:

`HF_TOKEN=your_hf_token`

---

## Variable reference (by `.env.example` section)

### `[api]`

| Variable | Purpose |
|----------|---------|
| `API_KEY` | Bearer key for this project’s API; also wired to Weaviate `WEAVIATE_LD_API_KEY`, MCP `MCP_API_KEY`, etc. (see compose). |
| `USE_MOCK_DB` | When `true`, some paths use a mock DB; set `false` for real Weaviate-backed behavior (`retrieval`, `scrape`, etc.). |
| `URL_HOST` | Public base URL for download/file links in responses; often `http://localhost:8080/f/`. |

### `[provider]` (Gemini: chat / image description)

| Variable | Purpose |
|----------|---------|
| `GEMINI_BASE_URL` | Generative Language API base URL (default: Google). |
| `GEMINI_API_KEY` | Gemini API key. |
| `GEMINI_MODEL` | Model id, e.g. `gemini-flash-latest`. |

### `[scrape]` (`POST /scrape`, Mercury Parser)

| Variable | Purpose |
|----------|---------|
| `MERCURY_PARSER_URL` | Mercury Parser base URL on the Docker network. |
| `MERCURY_REQUEST_TIMEOUT` | HTTP timeout (seconds) when calling Mercury. |

Optional compose-only: **`SCRAPE_CACHE_TTL_SECONDS`** (not in `.env.example`; has a default).

### `[search]` / `[searxng]`

| Variable | Purpose |
|----------|---------|
| `SEARCH_MAX_RESULT_LIMIT` | Cap for generic search results. |
| `NEWS_MAX_RESULT_LIMIT` | Cap for news-related results. |
| `MARKDOWN_CONVERTER_URL` | Markdown converter service URL during ingest (must match the converter container mount). |
| `MARKDOWN_CONVERTER_TIMEOUT` | Timeout (seconds) for that conversion request. |
| `SEARXNG_URL` | SearXNG base URL on the Docker network. |
| `SEARXNG_REQUEST_TIMEOUT` | Timeout (seconds) when calling SearXNG. |
| `SEARXNG_SECRET` | Maps to SearXNG `server.secret_key`; if unset, compose uses a built-in default (local testing only). |

### `[redis]`

| Variable | Purpose |
|----------|---------|
| `REDIS_HOST` / `REDIS_PORT` / `REDIS_DB` | Redis connection. |
| `CACHE_EXPIRATION_SECONDS` | Shared cache TTL (seconds); some modules define additional TTL env vars. |

### `[weaviate]`

| Variable | Purpose |
|----------|---------|
| `WEAVIATE_HOST` / `WEAVIATE_PORT` / `WEAVIATE_GRPC_PORT` | Used by the API Weaviate client. |
| `WEAVIATE_URL` | Mainly for `weaviate_ui` and other consumers that need a full HTTP URL; compose may override UI defaults. |

Query tuning can also use defaults or extras such as `DATABASE_QUERY_*` and `DATABASE_COLLECTION_NAME`; not all are listed in `.env.example`.

### `[markdown]` (conversion and image description)

| Variable | Purpose |
|----------|---------|
| `IMAGE_DESCRIPTION_ENABLED` | Enable image descriptions (read as a string; typically `true` / `false`). |
| `IMAGE_DESCRIBE_MIN_EDGE_PX` | Minimum shortest-edge size in pixels; smaller images may skip description to save cost. |

### `[embedding]`

| Variable | Purpose |
|----------|---------|
| `EMBEDDING_ENGINE` | `tei` (local TEI) or `gemini`. |
| `GEMINI_EMBEDDING_BASE_URL` | Optional; **embedding-only** REST base. Do not reuse `[provider]` `GEMINI_BASE_URL` unless that host also serves embedding APIs such as `embedContent`. |
| `GEMINI_EMBEDDING_MODEL` | Embedding model id. |
| `GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY` | Optional output size (model-dependent, e.g. 768, 1536, 3072). |
| `GEMINI_EMBEDDING_TASK_TYPE_QUERY` / `GEMINI_EMBEDDING_TASK_TYPE_DOCUMENT` | Task types for models that support them (e.g. `gemini-embedding-001`). |

When **`EMBEDDING_ENGINE=gemini`**, set **`GEMINI_API_KEY`** (shared with `[provider]`).

### `[tei]` (Text Embeddings Inference)

| Variable | Purpose |
|----------|---------|
| `TEI_ENDPOINT` | TEI HTTP endpoint. |
| `SERVICE_CHECK_INTERVAL` | Poll interval (seconds) while waiting for the embedding service. |
| `SERVICE_CHECK_TIMEOUT` | Per-check HTTP timeout (seconds). |

---

## Local scripts and tests

Some shell scripts run `source .env`. Plain POSIX/bash **`source` does not understand INI section lines**; if a script fails, use a file with only `export KEY=value` or `KEY=value` lines, or `export` required variables before running the command.

For HTTP and knowledge-base layout, see [`documents/API.md`](API.md) and [`documents/CONFIG.md`](CONFIG.md).
