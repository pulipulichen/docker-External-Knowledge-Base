#!/usr/bin/env bash
# MCP 整合測試：scrape_web_page（MCP_TEST_SCRAPE_*）
set -euo pipefail
export MCP_TEST_TOOL=scrape_web_page
# shellcheck source=test/mcp-test-docker-common.sh
source "$(cd "$(dirname "$0")" && pwd)/mcp-test-docker-common.sh"
