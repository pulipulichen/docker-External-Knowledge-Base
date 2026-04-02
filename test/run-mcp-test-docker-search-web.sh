#!/usr/bin/env bash
# MCP 整合測試：search_web（MCP_TEST_WEB_*）
set -euo pipefail
export MCP_TEST_TOOL=search_web
# shellcheck source=test/mcp-test-docker-common.sh
source "$(cd "$(dirname "$0")" && pwd)/mcp-test-docker-common.sh"
