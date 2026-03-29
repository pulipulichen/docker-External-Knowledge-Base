
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

You can call the `/search` endpoint using `curl`:

```bash
curl -X POST http://localhost:8080/search \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -d '{
       "query": "hello world"
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

`POST /news` fetches [Google News RSS search](https://news.google.com/rss/search) and returns a **JSON array** of items (same order as the RSS `<item>` elements). Each element has `title`, `link`, `pubDate`, and **`description`**: the original HTML description is turned into **Markdown** (numbered list when Google uses `<ol><li>…`), with **all hyperlinks removed** (anchor text kept; bare URLs stripped). There is no `guid` field and no `cached` flag in the response body. The upstream request sends the client IP via `X-Forwarded-For` / `X-Real-IP` when your reverse proxy sets them (same idea as `/search`).

**Authentication:** Bearer token (`Authorization: Bearer <YOUR_API_KEY>`), same as other API routes.

**JSON body**

| Field | Required | Description |
|-------|----------|-------------|
| `query` | Yes | Search keywords. |
| `hl` | No | UI / feed language (default: `zh-TW`). |
| `gl` | No | Region code (default: `TW`). |
| `ceid` | No | Google News `ceid` (default: `TW:zh-Hant`). |

**Successful response (200)**

- Top-level JSON **array** of objects: `{ "title", "link", "pubDate", "description" }` per RSS item (`description` rules as above).

Errors use the usual JSON `error` / `detail` fields (e.g. 401, 400, 502, 504).

**Caching:** Results are stored in Redis under keys prefixed with `news:rss:`, keyed by `(query, hl, gl, ceid)`. TTL defaults to **24 hours**; override with `NEWS_CACHE_TTL_SECONDS`. Connection uses the same `REDIS_HOST`, `REDIS_PORT`, and `REDIS_DB` as the rest of the API. Optional: `NEWS_REQUEST_TIMEOUT` (seconds, default `30`) for the Google RSS HTTP call.

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

Minimal body (defaults for `hl` / `gl` / `ceid`):

```bash
curl -X POST http://localhost:8080/news \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <YOUR_API_KEY>" \
     -d '{"query": "柯文哲"}'
```


