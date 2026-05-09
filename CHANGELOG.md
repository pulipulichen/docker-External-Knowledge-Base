# Changelog

## 0.0.2

- Added a fallback from file-based retrieval to standard database retrieval when file-mode lookup fails.
- Reduced noisy MCP knowledge base search output by disabling verbose successful-response debug printing.
- Reconnect and retry Weaviate update checks when the cached client has already been closed.
