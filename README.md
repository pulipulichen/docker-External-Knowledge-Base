
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

HTTP API usage for **Search**, **Scrape**, **News**, and **Knowledge base retrieval** (`/search`, `/scrape`, `/news`, `/retrieval`) is documented in [documents/API.md](documents/API.md).

Repository layout (`src/`, `knowledge_base/`, `test/`, and related paths) is described in [documents/STRUCTURE.md](documents/STRUCTURE.md).

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

