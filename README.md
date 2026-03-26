
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
       "url": "https://blog.pulipuli.info/2025/11/talk-deeply-felt-skypes-retirement.html"
     }'
```
