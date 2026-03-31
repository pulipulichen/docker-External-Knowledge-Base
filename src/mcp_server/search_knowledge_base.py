"""Call the API POST /retrieval endpoint from the MCP server."""

import json
import os

import requests


def search_knowledge_base(
    knowledge_id: str,
    query: str,
    top_k: int = 5,
    score_threshold: float = 0.1,
    file_mode: bool = False,
):
    """POST JSON to the internal retrieval API; Bearer token from MCP_API_KEY."""
    url = "http://api/retrieval"

    api_key = os.environ.get("MCP_API_KEY")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "knowledge_id": knowledge_id,
        "query": query,
        "retrieval_setting": {
            "top_k": top_k,
            "score_threshold": score_threshold,
        },
        "file_mode": file_mode,
    }

    print(json.dumps(payload, indent=4, ensure_ascii=False))

    try:
        # json=payload serializes the dict and sets Content-Type
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        print("Retrieval succeeded; response:")
        print(json.dumps(result, indent=4, ensure_ascii=False))
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


if __name__ == "__main__":
    search_knowledge_base()
