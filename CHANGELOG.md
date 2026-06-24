# Changelog

## 0.0.3

- Added spreadsheet `index_fields` support so indexed text and vectors can be limited to selected columns.
- Added configurable `display_fields` output with per-request overrides for retrieval responses.
- Kept field-limited spreadsheet retrieval compatible with hybrid Weaviate search.
- Fixed MCP tool schema compatibility for Gemini function calling by removing nullable union typing from `display_fields`.

## 0.0.2

- Added a fallback from file-based retrieval to standard database retrieval when file-mode lookup fails.
- Reduced noisy MCP knowledge base search output by disabling verbose successful-response debug printing.
- Reconnect and retry Weaviate update checks when the cached client has already been closed.
