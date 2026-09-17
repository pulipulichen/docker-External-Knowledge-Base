# Changelog

## 0.0.3

- Added cross-process and cross-thread file locking (`fcntl.flock`) for file staging to prevent race conditions during concurrent ingestion and worksheet inspection.
- Added shell streaming (`cat`) fallback for staging files from FUSE Google Drive mounts that report zero file size.
- Optimized `get_section_name` to return the configured `section` directly without reading files when defined in configuration.
- Added persistent local caching with graceful fallback for mounted spreadsheets to eliminate repeated rclone reads and avoid Input/output errors.
- Documented `--vfs-cache-mode full` for rclone Google Drive mounts and direct Google Sheets URL alternatives.
- Added Nginx proxy routes for MCP OAuth protected-resource and authorization-server metadata discovery.
- Added spreadsheet `index_fields` support so indexed text and vectors can be limited to selected columns.
- Added configurable `display_fields` output with per-request overrides for retrieval responses.
- Kept field-limited spreadsheet retrieval compatible with hybrid Weaviate search.
- Fixed MCP tool schema compatibility for Gemini function calling by removing nullable union typing from `display_fields`.

## 0.0.2

- Added a fallback from file-based retrieval to standard database retrieval when file-mode lookup fails.
- Reduced noisy MCP knowledge base search output by disabling verbose successful-response debug printing.
- Reconnect and retry Weaviate update checks when the cached client has already been closed.
