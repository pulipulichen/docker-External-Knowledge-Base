"""容器內 MCP 整合測試：Bearer 登入後依 MCP_TEST_TOOL 呼叫單一 tool。

- search_news：查新聞（預設 fulltext=true；設 MCP_TEST_NEWS_FULLTEXT=false 可只測 RSS）。
- search_web：網搜（預設 fulltext=false；見 MCP_TEST_WEB_*）。
- scrape_web_page：單頁擷取（見 MCP_TEST_SCRAPE_URL）。
- search_knowledge_base / kb_chunks：chunk 檢索，實際呼叫 search_{MCP_TEST_KB_ID}_chunks（見 MCP_TEST_KB_*）。
- kb_files：file 模式，呼叫 search_{MCP_TEST_KB_ID}_files。
"""

from __future__ import annotations

import asyncio
import json
import os
import socket
import sys
import time
from typing import Any
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


def _truthy_env(name: str, default: str) -> bool:
    v = os.environ.get(name, default).strip().lower()
    return v in ("1", "true", "yes", "on")


def _print_and_check_result(result: Any, *, label: str) -> None:
    if getattr(result, "is_error", False):
        print("MCP tools/call 回報 is_error", file=sys.stderr)
        sys.exit(2)

    print(f"--- {label} 回傳 ---")
    for block in getattr(result, "content", []) or []:
        text = getattr(block, "text", None)
        if text is not None:
            print(text)
        else:
            print(block)

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
                print(f"{label} 內容含 error:", data["error"], file=sys.stderr)
                sys.exit(2)
        except json.JSONDecodeError:
            pass


async def _run() -> None:
    mcp_url = os.environ.get("MCP_URL", "http://mcp_server/mcp").rstrip("/")
    token = (os.environ.get("MCP_API_KEY") or "").strip()
    if not token:
        print("MCP_API_KEY 未設定", file=sys.stderr)
        sys.exit(1)

    tool = (os.environ.get("MCP_TEST_TOOL") or "search_news").strip().lower()
    kb_chunk_tools = frozenset({"kb_chunks", "search_knowledge_base"})
    kb_modes = kb_chunk_tools | frozenset({"kb_files"})
    builtin = frozenset({"search_news", "search_web", "scrape_web_page"})
    if tool not in builtin | kb_modes:
        opts = sorted(builtin | kb_modes)
        print(f"MCP_TEST_TOOL 必須為其一: {', '.join(opts)}", file=sys.stderr)
        sys.exit(1)

    parsed = urlparse(mcp_url if "://" in mcp_url else f"http://{mcp_url}")
    mcp_host = parsed.hostname or "mcp_server"
    mcp_port = parsed.port or 80

    api_host = os.environ.get("MCP_TEST_API_HOST", "api").strip() or "api"
    api_port = int(os.environ.get("MCP_TEST_API_PORT", "80"))

    _wait_tcp(mcp_host, mcp_port)
    _wait_tcp(api_host, api_port)

    transport = StreamableHttpTransport(
        url=mcp_url,
        headers={"Authorization": f"Bearer {token}"},
    )
    client = Client(transport)

    mcp_tool_name: str
    args: dict[str, Any]

    if tool == "search_news":
        mcp_tool_name = "search_news"
        query = os.environ.get(
            "MCP_TEST_NEWS_QUERY",
            "伊朗 戰爭 美國 結果",
        )
        news_fulltext = _truthy_env("MCP_TEST_NEWS_FULLTEXT", "true")
        args = {"query": query, "fulltext": news_fulltext}
        print(
            f"search_news: query={query!r}, fulltext={news_fulltext}",
            file=sys.stderr,
        )
    elif tool == "search_web":
        mcp_tool_name = "search_web"
        query = os.environ.get("MCP_TEST_WEB_QUERY", "hello world")
        web_fulltext = _truthy_env("MCP_TEST_WEB_FULLTEXT", "false")
        try:
            limit = int(os.environ.get("MCP_TEST_WEB_LIMIT", "5"))
        except ValueError:
            limit = 5
        args = {"query": query, "fulltext": web_fulltext, "limit": limit}
        print(
            f"search_web: query={query!r}, fulltext={web_fulltext}, limit={limit}",
            file=sys.stderr,
        )
    elif tool in kb_modes:
        kb_id = (os.environ.get("MCP_TEST_KB_ID") or "example").strip()
        if not kb_id:
            print("MCP_TEST_KB_ID 不可為空", file=sys.stderr)
            sys.exit(1)
        suffix = "files" if tool == "kb_files" else "chunks"
        mcp_tool_name = f"search_{kb_id}_{suffix}"
        query = (os.environ.get("MCP_TEST_KB_QUERY") or "webcam").strip()
        if not query:
            print("MCP_TEST_KB_QUERY 不可為空", file=sys.stderr)
            sys.exit(1)
        try:
            top_k = int(os.environ.get("MCP_TEST_KB_TOP_K", "5"))
        except ValueError:
            top_k = 5
        try:
            score_threshold = float(os.environ.get("MCP_TEST_KB_SCORE_THRESHOLD", "0.1"))
        except ValueError:
            score_threshold = 0.1
        args = {
            "query": query,
            "top_k": top_k,
            "score_threshold": score_threshold,
        }
        print(
            f"{mcp_tool_name}: knowledge_id={kb_id!r}, query={query!r}, "
            f"top_k={top_k}, score_threshold={score_threshold}",
            file=sys.stderr,
        )
    else:
        mcp_tool_name = "scrape_web_page"
        url = (os.environ.get("MCP_TEST_SCRAPE_URL") or "").strip() or "https://example.com/"
        content_type = (os.environ.get("MCP_TEST_SCRAPE_CONTENT_TYPE") or "").strip()
        headers = (os.environ.get("MCP_TEST_SCRAPE_HEADERS") or "").strip()
        args = {"url": url}
        if content_type:
            args["content_type"] = content_type
        if headers:
            args["headers"] = headers
        print(f"scrape_web_page: url={url!r}", file=sys.stderr)

    async with client:
        result = await client.call_tool(mcp_tool_name, args)

    _print_and_check_result(result, label=mcp_tool_name)


def main() -> None:
    asyncio.run(_run())


if __name__ == "__main__":
    main()
