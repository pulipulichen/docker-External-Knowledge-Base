#!/usr/bin/env bash
# MCP 整合測試：知識庫 chunk 檢索（內部呼叫 search_${MCP_TEST_KB_ID}_chunks；預設 example + webcam）
set -euo pipefail
export MCP_TEST_TOOL=search_knowledge_base
# shellcheck source=test/mcp-test-docker-common.sh
source "$(cd "$(dirname "$0")" && pwd)/mcp-test-docker-common.sh"
