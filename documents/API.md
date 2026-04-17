# API usage examples

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
| `disable_metadata` | No | JSON boolean, default **`false`** for direct HTTP calls. If **`true`**, each object in **`records`** is returned **without** a **`metadata`** field (smaller responses). The MCP helper `search_knowledge_base` sends **`true`** by default so tool output stays lean unless you opt in. |

**MCP:** The server registers one pair of tools per config file: **`search_<knowledge_id>_chunks`** and **`search_<knowledge_id>_files`**. Both call the internal helper `search_knowledge_base`, which `POST`s to `http://api/retrieval` inside Compose with the same JSON shape (Bearer **`MCP_API_KEY`** must match your API key). Tool arguments map to `query`, `top_k`, `score_threshold`, `file_mode` on the files variant, and **`disable_metadata`** (default **`true`** on the tools, forwarded as the top-level JSON field). Direct HTTP callers who omit **`disable_metadata`** get **`false`** (metadata included).

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

## Reset knowledge base (`/reset`)

`POST /reset` removes the **Weaviate collection** named after the config stem (same collection naming as retrieval) and deletes **local generated artifacts**: the markdown cache under `knowledge_base/files/.md/` (single file for file-mode configs, or the `{file_name}-index` directory for directory-mode configs) and the **index timestamp** file under `knowledge_base/files/.time/` (`index_time_filepath` from the YAML-driven config).

**Authentication:** Bearer token (`Authorization: Bearer <YOUR_API_KEY>`), same as `/retrieval`.

**JSON body**

| Field | Required | Description |
|-------|----------|-------------|
| `knowledge_id` | Yes* | Same as `/retrieval`: config stem, optional `!section` for spreadsheets (only the stem is used for the Weaviate collection name and paths). |
| `reset_all` | No | If JSON boolean `true`, resets **every** knowledge base: deletes **all** Weaviate collections (`weaviate_reset_all` / client `delete_all`), then for each `*.yml` / `*.yaml` stem under `knowledge_base/configs/`, removes that KB’s generated `.md` / `.time` artifacts (same rules as a single-ID reset). Mutually exclusive with a targeted `knowledge_id` request; when `reset_all` is `true`, `knowledge_id` is ignored. |

\*Required unless `reset_all` is `true`.

**`USE_MOCK_DB`:** When `true`, the handler **does not** call Weaviate (no collection deletion); it still removes `.md` / `.time` artifacts when present. When `false`, it calls `weaviate_collection_delete` for that `knowledge_id`.

**Successful response (200)** for a single ID: JSON includes `knowledge_id`, `weaviate` (either `skipped` with reason, or `collection_existed` after delete), and `filesystem` with `markdown_removed`, `index_time_removed`, and `paths_removed` (list of paths that were removed).

**Successful response (200)** for `reset_all`: JSON includes `reset_all: true`, `weaviate` with `deleted_collections` (names removed) and `count`, and `filesystem` mapping each config stem to the same artifact-removal object as single-ID reset (or an `error` string if cleanup failed for that ID).

**Errors:** `401` unauthorized, `400` missing/invalid `knowledge_id` (when `reset_all` is not `true`), `404` unknown config, `502` if Weaviate deletion throws (when not in mock mode).

Example:

```bash
curl -X POST http://localhost:8080/reset \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"knowledge_id": "example"}'
```

Reset all Weaviate collections and all config-driven artifacts:

```bash
curl -X POST http://localhost:8080/reset \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"reset_all": true}'
```

## Ingest all configs (`/ingest/all`)

`POST /ingest/all` queues **ingest/index** for **every** `*.yml` / `*.yaml` stem under `knowledge_base/configs/`, in **sorted** order, **one knowledge base at a time** on a background thread. Each run uses `ingest_data` with **`section_name` unset** (`None`), so spreadsheet-style configs use the same default section resolution as other ingest paths (`get_section_name` inside `ingest_data` when `section_name` is `None`).

**Authentication:** Bearer token (`Authorization: Bearer <YOUR_API_KEY>`), same as `/retrieval` and `/reset`.

**JSON body (optional)**

| Field | Required | Description |
|-------|----------|-------------|
| `force_update` | No | JSON boolean, default **`true`**. When `true`, ingest proceeds even if automatic update checks would otherwise skip work (same idea as `POST /update` with `force_update`). When `false`, each KB follows `index_file` / `check_knowledge_base_need_update_automatically` behavior. |

**Response:** **`202 Accepted`** with `message`, `knowledge_ids`, `count`, and `force_update`. Processing continues asynchronously; the HTTP response does not wait for ingest to finish.

**Errors:** `401` unauthorized, `400` if `force_update` is present but not a JSON boolean, `404` if no config files exist under `knowledge_base/configs/`.

**curl** (host port **8080**):

```bash
curl -X POST http://localhost:8080/ingest/all \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -H "Content-Type: application/json" \
     -d '{"force_update": true}'
```

The retrieval demo page (`/demo/retrieval`) includes a button that calls this endpoint and shows a copyable cURL example.

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

Errors use JSON `error` / `detail` (e.g. 401, 400, 502, 504). With `fulltext: true` (the default), some Mercury failures after a successful SearXNG response may return **502** for the whole request (e.g. connection errors during full-text enrichment). Per-result Mercury **HTTP timeouts** drop full text for that hit only (snippet remains); they do not fail the entire search response.

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

### Maintaining blocked URL path suffixes (`/scrape`)

`POST /scrape` rejects requests when the **URL path** (not the query string) ends with a suffix listed as a non-web document (e.g. `.pdf`, `.docx`, `.csv`). Matching is **case-insensitive**. The API responds with **400** and JSON fields `error` / `detail` (including the disallowed suffix).

To add or remove extensions, edit **`src/api/python_packages/scrape/non_web_page_extensions.py`** and update the `NON_WEB_PAGE_EXTENSIONS` set. Each entry must be **lowercase** and **without** a leading dot (use `"pdf"`, not `".pdf"`). After changing the file, redeploy or restart the API container so the change takes effect.

When the Mercury Parser HTTP client times out (`MERCURY_REQUEST_TIMEOUT`), `POST /scrape` responds with **504** and an empty JSON object **`{}`** (no `error` / `detail` fields).

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
| `disable_cache` | No | Boolean, default `false`. If `true`, skip Redis read/write for the **news list** (`news:rss:*`); still uses per-URL Mercury scrape cache unless you clear Redis separately. |

**Successful response (200)**

- Top-level JSON **array** of objects per RSS item: at least `title`, `pubDate`, and `url` when present.
- When `fulltext` is `true` (the default), each object also has **`content`** (string or `null`).

Errors use the usual JSON `error` / `detail` fields (e.g. 401, 400, 502, 504). With `fulltext: true` (the default), some Mercury failures after a successful RSS fetch may return **502** for the whole request (e.g. connection errors during full-text enrichment). Per-item Mercury **HTTP timeouts** omit `content` for that item only; they do not fail the entire news response.

**Caching:** News results are stored in Redis under keys prefixed with `news:rss:`, keyed by **`(query, hl, gl, ceid, fulltext, limit)`**. TTL defaults to **24 hours** (`NEWS_CACHE_TTL_SECONDS`). Full-text extraction reuses scrape cache keys (`scrape:mercury:…`, `SCRAPE_CACHE_TTL_SECONDS`). Connection uses the same `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB` as the rest of the API. Optional: `NEWS_REQUEST_TIMEOUT` (seconds, default `30`) for the Google RSS HTTP call.

**MCP:** The `search_news` tool forwards **`fulltext`** (default `true`) and **`disable_cache`** (default `false`) to this endpoint.

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
