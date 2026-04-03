
# How to connect Google Drive as local file

```rclone mount
rclone mount gdrive:/documents /root/docker-External-Knowledge-Base/knowledge_base_files/.mnt/gdrive --daemon \
  --vfs-cache-mode off \
  --drive-export-formats "docx,xlsx,pdf" \
  --vfs-read-chunk-size 32M \
  --vfs-read-chunk-size-limit 2G \
  --vfs-read-wait 180s \
  --disable-http2
```

# Usage Examples

## Search API

`POST /search` proxies to **SearXNG** (JSON API) and returns a JSON object whose **`results`** array is trimmed to: `content` (snippet from SearXNG), `publishedDate`, `score`, `title`, `url`. The request forwards client IP via `X-Forwarded-For` / `X-Real-IP` when your reverse proxy sets them.

**Full text (default on):** By default (`fulltext` is `true` if omitted), each result’s **`url`** is followed through **Mercury Parser** (same service and Redis cache keys as `POST /scrape`, `contentType: markdown`). The SearXNG snippet is copied to **`snippet`**, then **`content`** is replaced with the article Markdown from Mercury (or `null` if there is no usable `url` or extraction failed). Set `"fulltext": false` for snippet-only results (faster; no Mercury per result).

**Authentication:** Bearer token (`Authorization: Bearer <YOUR_API_KEY>`), same as other API routes.

**JSON body (common fields)**

| Field | Required | Description |
|-------|----------|-------------|
| `query` | Yes | Search keywords. |
| `categories` | No | SearXNG category (e.g. `general`, `news`). |
| `language` | No | Language code (e.g. `zh-TW`, `en`). |
| `pageno` | No | Page number, default `1`. |
| `safesearch` | No | `0` / `1` / `2`, default `1`. |
| `time_range` | No | e.g. `day`, `week`, `month`, `year`. |
| `fulltext` | No | Boolean, default `true` (Mercury body as above). Set `false` for snippet-only. Must be a JSON boolean. |

Errors use JSON `error` / `detail` (e.g. 401, 400, 502, 504). With `fulltext: true` (the default), Mercury failure after a successful SearXNG response may return **502** or **504** for the whole request.

**MCP:** The `search_web` tool has a boolean **`fulltext`** argument (default `true`) forwarded to this endpoint.

Example:

```bash
curl -X POST http://localhost:8080/search \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -d '{
       "query": "hello world"
     }'
```

Example with full article text per result:

```bash
curl -X POST http://localhost:8080/search \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -d '{
       "query": "hello world",
       "fulltext": true
     }'
```

## Scrape API

You can call the `/scrape` endpoint using `curl`:

```bash
curl -X POST http://localhost:8080/scrape \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -d '{
       "url": "https://www.bbc.com/news/articles/c747x7gz249o"
     }'
```

## News API

`POST /news` fetches [Google News RSS search](https://news.google.com/rss/search) and returns a **JSON array** of items (same order as the RSS `<item>` elements). Each object includes **`title`**, **`pubDate`**, and **`url`** when the feed provides an item link (mapped from RSS `<link>`; typically a Google News redirect URL). There is no `guid` or `cached` field in the response body. The upstream RSS request sends the client IP via `X-Forwarded-For` / `X-Real-IP` when your reverse proxy sets them (same idea as `/search`).

**Full text (default on):** By default (`fulltext` is `true` if omitted), each item’s **`url`** is followed, the Google News redirect is resolved, and the article body is extracted with **Mercury Parser** (same service and Redis cache keys as `POST /scrape`, `contentType: markdown`). Each item then gets a **`content`** field (Markdown string from Mercury, or `null` if there is no `url` or extraction failed). Set `"fulltext": false` for RSS-only items (faster). Mercury timeouts use `MERCURY_REQUEST_TIMEOUT` (see Scrape / environment docs).

**Authentication:** Bearer token (`Authorization: Bearer <YOUR_API_KEY>`), same as other API routes.

**JSON body**

| Field | Required | Description |
|-------|----------|-------------|
| `query` | Yes | Search keywords. |
| `hl` | No | UI / feed language (default: `zh-TW`). |
| `gl` | No | Region code (default: `TW`). |
| `ceid` | No | Google News `ceid` (default: `TW:zh-Hant`). |
| `fulltext` | No | Boolean, default `true` (`content` per item via Mercury; see above). Set `false` for titles/links only. Must be a JSON boolean. |

**Successful response (200)**

- Top-level JSON **array** of objects per RSS item: at least `title`, `pubDate`, and `url` when present.
- When `fulltext` is `true` (the default), each object also has **`content`** (string or `null`).

Errors use the usual JSON `error` / `detail` fields (e.g. 401, 400, 502, 504). With `fulltext: true` (the default), a Mercury failure after a successful RSS fetch may return **502** or **504** for the whole request.

**Caching:** News results are stored in Redis under keys prefixed with `news:rss:`, keyed by **`(query, hl, gl, ceid, fulltext)`**. TTL defaults to **24 hours** (`NEWS_CACHE_TTL_SECONDS`). Full-text extraction reuses scrape cache keys (`scrape:mercury:…`, `SCRAPE_CACHE_TTL_SECONDS`). Connection uses the same `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB` as the rest of the API. Optional: `NEWS_REQUEST_TIMEOUT` (seconds, default `30`) for the Google RSS HTTP call.

**MCP:** The `search_news` tool accepts the same idea via a boolean **`fulltext`** argument (default `true`) and forwards it to this endpoint.

Example with `curl`:

```bash
curl -X POST http://localhost:8080/news \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -d '{
       "query": "climate",
       "hl": "zh-TW",
       "gl": "TW",
       "ceid": "TW:zh-Hant"
     }'
```

Example with full article text:

```bash
curl -X POST http://localhost:8080/news \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -d '{
       "query": "climate",
       "fulltext": true
     }'
```

## Knowledge base retrieval API

`POST /retrieval` runs semantic retrieval against a configured knowledge base (chunk mode by default, or file mode when requested). Behavior depends on **`USE_MOCK_DB`**: when `true` (default in many setups), the handler returns **mock** results for local testing; when `false`, it queries **Weaviate** using the config under `knowledge_base/configs/`.

**Authentication:** Bearer token (`Authorization: Bearer <YOUR_API_KEY>`), same as `/search`, `/news`, and `/scrape`.

**JSON body**

| Field | Required | Description |
|-------|----------|-------------|
| `knowledge_id` | Yes | Config stem: the YAML filename in `knowledge_base/configs/` without extension (e.g. `example` → `example.yml`). For spreadsheet-style sources you can pass `my_kb!SheetName` so the part after `!` is the section/sheet name (see `parse_knowledge_id` in the API). |
| `query` | Yes | Natural language or keywords to retrieve against. |
| `retrieval_setting` | No | Object with optional `top_k` (default **5**) and `score_threshold` (default **no filter** in the HTTP handler when omitted; MCP defaults **0.1** when calling the helper). |
| `file_mode` | No | JSON boolean, default **`false`**. If **`true`**, use file-level retrieval instead of chunk retrieval. |

**MCP:** The server registers one pair of tools per config file: **`search_<knowledge_id>_chunks`** and **`search_<knowledge_id>_files`**. Both call the internal helper `search_knowledge_base`, which `POST`s to `http://api/retrieval` inside Compose with the same JSON shape (Bearer **`MCP_API_KEY`** must match your API key). Tool arguments map to `query`, `top_k`, `score_threshold`, and `file_mode` on the files variant.

**curl** (host port **8080** maps to the API container; use **`API_KEY`** from `.env`):

```bash
curl -X POST http://localhost:8080/retrieval \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{
       "knowledge_id": "example",
       "query": "webcam",
       "retrieval_setting": {
         "top_k": 5,
         "score_threshold": 0.1
       }
     }'
```

**File mode** (same endpoint, set `file_mode` to JSON boolean `true`):

```bash
curl -X POST http://localhost:8080/retrieval \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{
       "knowledge_id": "example",
       "query": "webcam",
       "file_mode": true,
       "retrieval_setting": {
         "top_k": 5,
         "score_threshold": 0.1
       }
     }'
```

**Smoke test:** `./test/run-test-search-knowledge-base.sh` sources `.env`, ensures Docker Compose is up, then posts the chunk-style payload above twice (10 seconds apart) against `http://localhost:8080/retrieval`.

## MCP integration tests (Docker)

These scripts run **inside Docker** (the `mcp_test` service installs `fastmcp` in the image). You do **not** need Python MCP packages on the host. They bring up the stack with profile **`mcp-test`**, execute one MCP tool call with Bearer auth, then stop services when the test container exits (`--abort-on-container-exit`).

**Prerequisites:** working Docker Compose setup, project `.env` with **`API_KEY`** (same token the MCP server expects). The scripts use `sudo docker compose`; adjust if your environment runs Docker without `sudo`.

**Note:** `sudo` normally drops environment variables, so which MCP tool runs is passed with `sudo env MCP_TEST_TOOL=…` inside `mcp-test-docker-common.sh`. If you bypass that script, set `MCP_TEST_TOOL` in the project `.env` (Compose reads it for interpolation) or use `sudo -E` / `sudo env …` yourself.

**Entry scripts** (from the repository root):

| Script | MCP tool exercised |
|--------|-------------------|
| `./test/run-mcp-test-docker-search-news.sh` | `search_news` |
| `./test/run-mcp-test-docker-search-web.sh` | `search_web` |
| `./test/run-mcp-test-docker-scrape-web-page.sh` | `scrape_web_page` |
| `./test/run-mcp-test-docker-search-knowledge-base.sh` | `search_{knowledge_id}_chunks` (chunk retrieval; default knowledge id `example`) |

Shared logic lives in `test/mcp-test-docker-common.sh` (sourced by the scripts above).

**Optional environment variables** (host `.env` or `export` before running; defaults are set in `docker-compose.yml` for the `mcp_test` service):

| Variable | Used when | Description |
|----------|-----------|-------------|
| `MCP_TEST_NEWS_QUERY` | news test | RSS search query. |
| `MCP_TEST_NEWS_FULLTEXT` | news test | `true` / `1` / `yes` / `on` to fetch full article text via Mercury (see compose defaults). |
| `MCP_TEST_WEB_QUERY` | web search test | Search keywords. |
| `MCP_TEST_WEB_FULLTEXT` | web search test | Same truthy convention; default `true` in compose. |
| `MCP_TEST_WEB_LIMIT` | web search test | Max hits (integer). |
| `MCP_TEST_SCRAPE_URL` | scrape test | URL passed to `scrape_web_page`. |
| `MCP_TEST_SCRAPE_CONTENT_TYPE` | scrape test | Optional Mercury `contentType` (empty to omit). |
| `MCP_TEST_SCRAPE_HEADERS` | scrape test | Optional URL-encoded headers (empty to omit). |
| `MCP_TEST_KB_ID` | knowledge base test | Config stem under `knowledge_base/configs/` (e.g. `example` → tool `search_example_chunks`). |
| `MCP_TEST_KB_QUERY` | knowledge base test | Retrieval query string. |
| `MCP_TEST_KB_TOP_K` | knowledge base test | Top-k for retrieval. |
| `MCP_TEST_KB_SCORE_THRESHOLD` | knowledge base test | Minimum similarity score. |

**Knowledge base file mode:** the test runner also accepts `MCP_TEST_TOOL=kb_files` (tool `search_{MCP_TEST_KB_ID}_files`). There is no dedicated shell script for it; run:

```bash
export MCP_TEST_TOOL=kb_files
docker compose --profile mcp-test up --build --abort-on-container-exit
```

**If the stack is already running**, you can run only the test container (set `MCP_TEST_TOOL` as needed):

```bash
docker compose --profile mcp-test run --rm mcp_test
```

