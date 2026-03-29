from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

import itertools
import os
from pathlib import Path

import yaml
from pydantic import Field
from typing import Annotated

from search_knowledge_base import search_knowledge_base
from scrape_web_page import scrape_web_page
from search_news import search_news
from search_web import search_web

MCP_API_KEY = os.getenv("MCP_API_KEY")

# Only this bearer token is accepted
verifier = StaticTokenVerifier(
    tokens={
        MCP_API_KEY: {
            "client_id": "rps-client",
            "scopes": ["rps:play"],
        }
    },
    # Optional scope checks; empty list means no scope enforcement
    required_scopes=[],
)

mcp = FastMCP(name="external-knowledge-base", auth=verifier)

# ===========================


def load_knowledge_base_configs(directory):
    kb_list = []

    if not directory.exists():
        print(f"Error: directory not found: {directory}")
        return []

    yaml_files = sorted(
        itertools.chain(directory.glob("*.yml"), directory.glob("*.yaml"))
    )

    for file_path in yaml_files:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f)

                name = file_path.stem
                description = content.get("description", "No description")

                kb_list.append((name, description))

        except Exception as e:
            print(f"Error reading {file_path.name}: {e}")

    return kb_list


BASE_DIR = Path("/knowledge_base_configs")
knowledge_base_types = load_knowledge_base_configs(BASE_DIR)

# ===========================


def make_tool_function(reg_key, reg_desc):
    """Build a tool function with reg_key closed over (one tool per knowledge base config)."""

    def dynamic_tool(
        query: Annotated[
            str,
            Field(
                description=(
                    "Question or keywords to search; can be a short phrase, "
                    "e.g. how overtime pay is calculated"
                ),
            ),
        ],
        top_k: Annotated[
            int,
            Field(description="Number of top matches to return (default 5)"),
        ] = 5,
        score_threshold: Annotated[
            float,
            Field(
                description=(
                    "Minimum similarity score (0.0–1.0); results below this are dropped (default 0.1)"
                ),
            ),
        ] = 0.1,
    ) -> str:
        return search_knowledge_base(reg_key, query, top_k, score_threshold)

    # MCP uses the Python function name as the tool id; must be unique per tool
    dynamic_tool.__name__ = f"search_{reg_key}_rules"

    dynamic_tool.__doc__ = f"{reg_desc} Pass a query or keywords to search this knowledge base."

    return dynamic_tool


for key, desc in knowledge_base_types:
    tool_func = make_tool_function(key, desc)
    mcp.tool()(tool_func)

    print(f"Registered tool: {tool_func.__name__}")

# ===========================


def scrape_web_page_tool(
    url: Annotated[
        str,
        Field(
            description="Page URL whose main content to extract (articles, news, blogs, etc.)",
        ),
    ],
    content_type: Annotated[
        str | None,
        Field(
            description="Optional contentType query parameter for Mercury Parser",
        ),
    ] = None,
    headers: Annotated[
        str | None,
        Field(
            description="Optional URL-encoded HTTP headers string (see mercury-parser API docs)",
        ),
    ] = None,
) -> str:
    """Extract main readable content (title, article HTML, excerpt, etc.) via Mercury Parser."""
    return scrape_web_page(url, content_type, headers)


scrape_web_page_tool.__name__ = "scrape_web_page"
mcp.tool()(scrape_web_page_tool)
print(f"Registered tool: {scrape_web_page_tool.__name__}")

# ===========================


def search_web_tool(
    query: Annotated[
        str,
        Field(description="Web search keywords or a full question"),
    ],
    categories: Annotated[
        str | None,
        Field(
            description="Optional SearXNG category (e.g. general, images, news)",
        ),
    ] = None,
    language: Annotated[
        str | None,
        Field(
            description="Optional language code (e.g. zh-TW, en)",
        ),
    ] = None,
    pageno: Annotated[
        int,
        Field(description="Result page number, starting at 1"),
    ] = 1,
    safesearch: Annotated[
        int | None,
        Field(description="Optional safe search: 0 off, 1 moderate, 2 strict"),
    ] = None,
    time_range: Annotated[
        str | None,
        Field(
            description="Optional time range (e.g. day, week, month, year)",
        ),
    ] = None,
) -> str:
    """Search the public web via SearXNG; returns titles, URLs, snippets, etc."""
    return search_web(
        query,
        categories=categories,
        language=language,
        pageno=pageno,
        safesearch=safesearch,
        time_range=time_range,
    )


search_web_tool.__name__ = "search_web"
mcp.tool()(search_web_tool)
print(f"Registered tool: {search_web_tool.__name__}")

# ===========================


def search_news_tool(
    query: Annotated[
        str,
        Field(description="News search keywords or topic (Google News RSS)"),
    ],
    hl: Annotated[
        str | None,
        Field(
            description="Optional feed language (default on API: zh-TW), e.g. en-US",
        ),
    ] = None,
    gl: Annotated[
        str | None,
        Field(
            description="Optional region code (default on API: TW), e.g. US",
        ),
    ] = None,
    ceid: Annotated[
        str | None,
        Field(
            description="Optional Google News ceid (default on API: TW:zh-Hant)",
        ),
    ] = None,
) -> str:
    """Fetch Google News headlines/snippets for a query; returns Markdown text (and cache metadata) as JSON."""
    return search_news(query, hl=hl, gl=gl, ceid=ceid)


search_news_tool.__name__ = "search_news"
mcp.tool()(search_news_tool)
print(f"Registered tool: {search_news_tool.__name__}")

# ===========================

if __name__ == "__main__":
    mcp.run(transport="http", port=80, host="0.0.0.0")
