"""Call the API POST /news endpoint (Google News RSS → Markdown) from the MCP server."""

import json
import os

import requests


def search_news(
    query: str,
    hl: str = "zh-TW",
    gl: str = "TW",
    ceid: str = "TW:zh-Hant",
    fulltext: bool = True,
    limit: int = 5,
    disable_cache: bool = False,
):
    """POST JSON to the internal API; Bearer token from MCP_API_KEY."""
    url = "http://api/news"

    api_key = os.environ.get("MCP_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict = {"query": query, "fulltext": fulltext, "limit": limit}
    if hl is not None:
        payload["hl"] = hl
    if gl is not None:
        payload["gl"] = gl
    if ceid is not None:
        payload["ceid"] = ceid
    if disable_cache:
        payload["disable_cache"] = True

    # print(json.dumps(payload, indent=4, ensure_ascii=False))

    timeout = 300 if fulltext else 90
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        print("News search succeeded; item_count:", len(result) if isinstance(result, list) else 0)
        return json.dumps(result, ensure_ascii=False)

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if "response" in locals() and response.content:
            print(f"Error body: {response.text}")

        return json.dumps(
            {
                "error": str(e),
            },
            ensure_ascii=False,
        )
