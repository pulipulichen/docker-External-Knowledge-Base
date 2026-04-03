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
# Gemini function-calling rejects JSON Schema anyOf/null unions (e.g. str | None).
# Use plain str/int here and map sentinels to None when calling API helpers.


def _optional_str(value: str) -> str | None:
    s = value.strip()
    return s if s else None


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


def make_tool_function(reg_key, reg_desc, file_mode: bool = False):
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
        return search_knowledge_base(reg_key, query, top_k, score_threshold, file_mode)

    # MCP uses the Python function name as the tool id; must be unique per tool
    if file_mode is False:
        dynamic_tool.__name__ = f"search_{reg_key}_chunks"
    else:
        dynamic_tool.__name__ = f"search_{reg_key}_files"

    dynamic_tool.__doc__ = f"{reg_desc} Pass a query or keywords to search this knowledge base."

    return dynamic_tool


for key, desc in knowledge_base_types:
    tool_func = make_tool_function(key, desc, False)
    mcp.tool()(tool_func)

    print(f"Registered tool: {tool_func.__name__}")

for key, desc in knowledge_base_types:
    tool_func = make_tool_function(key, desc, True)
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
        str,
        Field(description="Optional contentType for Mercury Parser; leave empty to omit"),
    ] = "",
    headers: Annotated[
        str,
        Field(
            description="Optional URL-encoded HTTP headers (mercury-parser API); leave empty to omit",
        ),
    ] = "",
) -> str:
    """Extract main readable content (title, article HTML, excerpt, etc.) via Mercury Parser."""
    return scrape_web_page(
        url, _optional_str(content_type), _optional_str(headers)
    )


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
        str,
        Field(
            description="Optional SearXNG category (e.g. general, images, news); empty to omit",
        ),
    ] = "",
    language: Annotated[
        str,
        Field(description="Optional language code (e.g. zh-TW, en); empty to omit"),
    ] = "",
    pageno: Annotated[
        int,
        Field(description="Result page number, starting at 1"),
    ] = 1,
    safesearch: Annotated[
        int,
        Field(
            description=(
                "Safe search: 0 off, 1 moderate, 2 strict; use -1 to omit (default)"
            ),
        ),
    ] = -1,
    time_range: Annotated[
        str,
        Field(
            description="Optional time range (e.g. day, week, month, year); empty to omit",
        ),
    ] = "",
    fulltext: Annotated[
        bool,
        Field(
            description=(
                "If true (default), fetch each result URL through Mercury and put article markdown "
                "in content (SearXNG excerpt moves to snippet); set false for snippet-only, faster"
            ),
        ),
    ] = True,
    limit: Annotated[
        int,
        Field(
            description=(
                "Maximum number of search hits to return in results (default 5; "
                "API caps at SEARCH_MAX_RESULT_LIMIT, typically 50)"
            ),
        ),
    ] = 5,
) -> str:
    """Search the public web via SearXNG; with fulltext, each result has snippet + Mercury content."""
    return search_web(
        query,
        categories=_optional_str(categories),
        language=_optional_str(language),
        pageno=pageno,
        safesearch=safesearch if safesearch >= 0 else None,
        time_range=_optional_str(time_range),
        fulltext=fulltext,
        limit=limit,
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
        str,
        Field(
            description="Optional feed language (API default zh-TW), e.g. en-US; empty to omit",
        ),
    ] = "",
    gl: Annotated[
        str,
        Field(
            description="Optional region code (API default TW), e.g. US; empty to omit",
        ),
    ] = "",
    ceid: Annotated[
        str,
        Field(
            description="Optional Google News ceid (API default TW:zh-Hant); empty to omit",
        ),
    ] = "",
    fulltext: Annotated[
        bool,
        Field(
            description=(
                "If true (default), follow each item's url and extract article body via Mercury "
                "into a content field (markdown); set false for RSS-only, faster"
            ),
        ),
    ] = True,
    limit: Annotated[
        int,
        Field(
            description=(
                "Maximum number of news items to return (default 5; API caps at NEWS_MAX_RESULT_LIMIT, typically 50)"
            ),
        ),
    ] = 5,
    disable_cache: Annotated[
        bool,
        Field(
            description=(
                "If true, skip Redis cache for this news list (always refetch RSS and re-run fulltext); "
                "does not disable per-URL Mercury scrape cache"
            ),
        ),
    ] = False,
) -> str:
    """Fetch Google News as a JSON array of items (title, url, pubDate); with fulltext, each item also has content from Mercury."""
    return search_news(
        query,
        hl=_optional_str(hl),
        gl=_optional_str(gl),
        ceid=_optional_str(ceid),
        fulltext=fulltext,
        limit=limit,
        disable_cache=disable_cache,
    )


search_news_tool.__name__ = "search_news"
mcp.tool()(search_news_tool)
print(f"Registered tool: {search_news_tool.__name__}")

# ===========================

if __name__ == "__main__":
    mcp.run(transport="http", port=80, host="0.0.0.0")
