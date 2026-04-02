"""容器內 MCP 測試：Bearer 登入後呼叫 search_news（查未來一週天氣相關新聞）。

預設會帶 fulltext=true（經 API 以 Mercury 抓全文）；若要只測 RSS 列表、加快執行，請設
環境變數 MCP_TEST_NEWS_FULLTEXT=false（或 0、no、off）。
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import time
from urllib.parse import urlparse

from fastmcp import Client
from fastmcp.client.transports import StreamableHttpTransport


def _wait_tcp(host: str, port: int, *, attempts: int = 60, delay_sec: float = 2.0) -> None:
    for i in range(attempts):
        try:
            with socket.create_connection((host, port), timeout=5):
                return
        except OSError:
            pass
        if i + 1 < attempts:
            time.sleep(delay_sec)
    print(f"timeout: {host}:{port} 無法連線", file=sys.stderr)
    sys.exit(1)


async def _run() -> None:
    mcp_url = os.environ.get("MCP_URL", "http://mcp_server/mcp").rstrip("/")
    token = (os.environ.get("MCP_API_KEY") or "").strip()
    if not token:
        print("MCP_API_KEY 未設定", file=sys.stderr)
        sys.exit(1)

    query = os.environ.get(
        "MCP_TEST_NEWS_QUERY",
        # "未來一週 天氣 預報",
        "伊朗 戰爭 美國 結果",
    )

    _ft = os.environ.get("MCP_TEST_NEWS_FULLTEXT", "true").strip().lower()
    news_fulltext = _ft not in ("0", "false", "no", "off", "")

    parsed = urlparse(mcp_url if "://" in mcp_url else f"http://{mcp_url}")
    mcp_host = parsed.hostname or "mcp_server"
    mcp_port = parsed.port or 80

    api_host = os.environ.get("MCP_TEST_API_HOST", "api").strip() or "api"
    api_port = int(os.environ.get("MCP_TEST_API_PORT", "80"))

    # search_news 會打 API；兩邊埠可連再上線
    _wait_tcp(mcp_host, mcp_port)
    _wait_tcp(api_host, api_port)

    transport = StreamableHttpTransport(
        url=mcp_url,
        headers={"Authorization": f"Bearer {token}"},
    )
    client = Client(transport)

    print(
        f"search_news: query={query!r}, fulltext={news_fulltext}",
        file=sys.stderr,
    )

    async with client:
        result = await client.call_tool(
            "search_news",
            {"query": query, "fulltext": news_fulltext},
        )

    if getattr(result, "is_error", False):
        print("MCP tools/call 回報 is_error", file=sys.stderr)
        sys.exit(2)

    print("--- search_news 回傳 ---")
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text is not None:
            print(text)
        else:
            print(block)

    # 若為 JSON 字串，順便檢查 API 層錯誤
    raw = None
    for block in getattr(result, "content", []) or []:
        t = getattr(block, "text", None)
        if isinstance(t, str) and t.strip().startswith("{"):
            raw = t
            break
    if raw:
        try:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("error"):
                print("search_news 內容含 error:", data["error"], file=sys.stderr)
                sys.exit(2)
        except json.JSONDecodeError:
            pass


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
