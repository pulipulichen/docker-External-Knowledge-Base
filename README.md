
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

**Optional full text:** Set `"fulltext": true` to follow each result’s **`url`** through **Mercury Parser** (same service and Redis cache keys as `POST /scrape`, `contentType: markdown`). The SearXNG snippet is copied to **`snippet`**, then **`content`** is replaced with the article Markdown from Mercury (or `null` if there is no usable `url` or extraction failed). This is slower and invokes Mercury once per result.

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
| `fulltext` | No | Boolean, default `false`. If `true`, add Mercury body as above. Must be a JSON boolean. |

Errors use JSON `error` / `detail` (e.g. 401, 400, 502, 504). With `fulltext: true`, Mercury failure after a successful SearXNG response may return **502** or **504** for the whole request.

**MCP:** The `search_web` tool has a boolean **`fulltext`** argument (default `false`) forwarded to this endpoint.

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

**Optional full text:** Set `"fulltext": true` to follow each item’s **`url`**, resolve the Google News redirect, and extract the article body with **Mercury Parser** (same service and Redis cache keys as `POST /scrape`, `contentType: markdown`). Each item then gets a **`content`** field (Markdown string from Mercury, or `null` if there is no `url` or extraction failed). This is slower and loads Mercury once per item; Mercury timeouts use `MERCURY_REQUEST_TIMEOUT` (see Scrape / environment docs).

**Authentication:** Bearer token (`Authorization: Bearer <YOUR_API_KEY>`), same as other API routes.

**JSON body**

| Field | Required | Description |
|-------|----------|-------------|
| `query` | Yes | Search keywords. |
| `hl` | No | UI / feed language (default: `zh-TW`). |
| `gl` | No | Region code (default: `TW`). |
| `ceid` | No | Google News `ceid` (default: `TW:zh-Hant`). |
| `fulltext` | No | Boolean, default `false`. If `true`, add `content` per item via Mercury (see above). Must be a JSON boolean. |

**Successful response (200)**

- Top-level JSON **array** of objects per RSS item: at least `title`, `pubDate`, and `url` when present.
- If `fulltext` was `true`, each object also has **`content`** (string or `null`).

Errors use the usual JSON `error` / `detail` fields (e.g. 401, 400, 502, 504). With `fulltext: true`, a Mercury failure after a successful RSS fetch may return **502** or **504** for the whole request.

**Caching:** News results are stored in Redis under keys prefixed with `news:rss:`, keyed by **`(query, hl, gl, ceid, fulltext)`**. TTL defaults to **24 hours** (`NEWS_CACHE_TTL_SECONDS`). Full-text extraction reuses scrape cache keys (`scrape:mercury:…`, `SCRAPE_CACHE_TTL_SECONDS`). Connection uses the same `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB` as the rest of the API. Optional: `NEWS_REQUEST_TIMEOUT` (seconds, default `30`) for the Google RSS HTTP call.

**MCP:** The `search_news` tool accepts the same idea via a boolean **`fulltext`** argument (default `false`) and forwards it to this endpoint.

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

