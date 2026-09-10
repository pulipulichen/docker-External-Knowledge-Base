# Demo Pages

The demo pages are served by the Flask API through the Nginx reverse proxy. They
are not a separate frontend service.

## Prerequisites

1. Install Docker Compose.
2. Create the project environment file:

   ```bash
   cp .env.example .env
   ```

3. Set a real `API_KEY` in `.env`.
4. From the repository root, start the stack:

   ```bash
   docker compose up --build -d
   ```

   If Docker requires elevated privileges on your host, use `sudo docker
   compose` instead.

## Open the demo pages

After the containers start, open one of these URLs in a browser:

- Knowledge base retrieval: <http://localhost:8080/demo/retrieval>
- Web search: <http://localhost:8080/demo/search>
- Web page scraping: <http://localhost:8080/demo/scrape>
- News search: <http://localhost:8080/demo/news>
- Knowledge base reset: <http://localhost:8080/demo/reset>

Each page provides an API key field. Paste the value of `API_KEY` from `.env`
into the page. The key is stored only in that browser's local storage and is
sent as a Bearer token when the page calls the API.

## Using each page

### Retrieval

Open `/demo/retrieval` to query a configured knowledge base. Select a Knowledge
ID, enter a query, and optionally configure:

- `top_k`
- `score_threshold`
- file-level retrieval
- metadata suppression
- display field overrides

The page also provides an **Index all configs** action. This queues ingestion
for every YAML configuration under `knowledge_base/configs/` and returns a
cURL example for the request.

### Web search

Open `/demo/search` to call `POST /search` through a form. Enter a query and
optionally set the category, language, page number, SafeSearch level, and time
range. Full-text enrichment is enabled by default and uses Mercury Parser, so
disabling it can make searches faster.

### Web page scraping

Open `/demo/scrape` to extract an article from a URL with Mercury Parser. The
page accepts an optional `contentType` and optional request headers in the
format expected by the parser. Direct document URLs such as PDF downloads may
be rejected by the API.

### News search

Open `/demo/news` to search Google News RSS. Enter a query and optionally change
the language, region, result limit, full-text enrichment, or server-side cache
behavior.

### Knowledge base reset

Open `/demo/reset` to reset one knowledge base or all knowledge bases. A reset
can delete Weaviate data and generated files under `knowledge_base/files/`.
Use this page only when that destructive operation is intentional.

## Supporting web interfaces

The stack also exposes these service interfaces:

- SearXNG: <http://localhost:40002>
- Weaviate UI: <http://localhost:47777>
These interfaces are separate from the five Flask demo pages above.

## Troubleshooting

Check the service state from the repository root:

```bash
docker compose ps
```

Follow the complete stack log if a page cannot be opened:

```bash
docker compose logs -f
```

For API-specific logs:

```bash
docker compose logs -f api
```

The API and demo pages are published through Nginx on host port `8080`. If that
port is already in use, change the host-side port mapping for the `nginx`
service in `docker-compose.yml`, then use the new port in the browser URL.
