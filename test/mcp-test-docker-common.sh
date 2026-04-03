#!/usr/bin/env bash
# 由各 run-mcp-test-docker-*.sh source；設定 MCP_TEST_TOOL 後拉起 stack 並跑 mcp_test。
# 本機不需安裝 fastmcp；測試結束後 --abort-on-container-exit 會停止相關服務。
# 若 stack 已在背景：docker compose --profile mcp-test run --rm mcp_test
set -euo pipefail
MCP_TEST_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$MCP_TEST_ROOT"
clear
# sudo 預設不保留 MCP_TEST_TOOL，compose 會誤用預設 search_news；須顯式傳入
# 先 teardown，避免殘留容器仍掛在已刪除的網路上（daemon: network ... not found）
sudo docker compose down --remove-orphans
sudo env "MCP_TEST_TOOL=${MCP_TEST_TOOL:-search_news}" \
	docker compose --profile mcp-test up --build --abort-on-container-exit
