#!/usr/bin/env bash
# MCP 整合測試：search_news（環境變數見 docker-compose mcp_test / MCP_TEST_NEWS_*）
set -euo pipefail
export MCP_TEST_TOOL=search_news
# shellcheck source=test/mcp-test-docker-common.sh
source "$(cd "$(dirname "$0")" && pwd)/mcp-test-docker-common.sh"
