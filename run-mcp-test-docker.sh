#!/usr/bin/env bash
# 全程在 Docker 內執行（mcp_test 映像內 pip 安裝 fastmcp），本機不需安裝套件。
# 會拉起依賴服務，mcp_test 容器啟動即跑測試；測試結束後因 --abort-on-container-exit 會一併停止所有服務。
# 若 stack 已在背景執行，可改為：docker compose --profile mcp-test run --rm mcp_test
set -euo pipefail
cd "$(dirname "$0")"
exec docker compose --profile mcp-test up --build --abort-on-container-exit
