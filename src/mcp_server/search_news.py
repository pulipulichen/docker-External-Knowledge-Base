"""Call the API POST /news endpoint (Google News RSS → Markdown) from the MCP server."""

import json
import os

import requests


def search_news(
    query: str,
    hl: str | None = None,
    gl: str | None = None,
    ceid: str | None = None,
):
    """POST JSON to the internal API; Bearer token from MCP_API_KEY."""
    url = "http://api/news"

    api_key = os.environ.get("MCP_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict = {"query": query}
    if hl is not None:
        payload["hl"] = hl
    if gl is not None:
        payload["gl"] = gl
    if ceid is not None:
        payload["ceid"] = ceid

    print(json.dumps(payload, indent=4, ensure_ascii=False))

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=90)
        response.raise_for_status()
        result = response.json()
        print("News search succeeded; response summary:")
        n = len(result.get("items") or [])
        print(json.dumps({"cached": result.get("cached"), "item_count": n}, ensure_ascii=False))
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
