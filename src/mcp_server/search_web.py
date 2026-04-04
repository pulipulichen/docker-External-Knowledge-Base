"""Call the API POST /search endpoint (SearXNG-backed) from the MCP server."""

import json
import os

import requests


def search_web(
    query: str,
    categories: str | None = None,
    language: str | None = None,
    pageno: int = 1,
    safesearch: int | None = None,
    time_range: str | None = None,
    fulltext: bool = True,
    limit: int = 5,
):
    """POST JSON to the internal API; Bearer token from MCP_API_KEY."""
    url = "http://api/search"

    api_key = os.environ.get("MCP_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict = {
        "query": query,
        "pageno": pageno,
        "fulltext": fulltext,
        "limit": limit,
    }
    if categories is not None:
        payload["categories"] = categories
    if language is not None:
        payload["language"] = language
    if safesearch is not None:
        payload["safesearch"] = safesearch
    if time_range is not None:
        payload["time_range"] = time_range

    # print(json.dumps(payload, indent=4, ensure_ascii=False))

    timeout = 300 if fulltext else 90
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
        response.raise_for_status()
        result = response.json()
        # print("Search succeeded; response:")
        # print(json.dumps(result, indent=4, ensure_ascii=False))
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
