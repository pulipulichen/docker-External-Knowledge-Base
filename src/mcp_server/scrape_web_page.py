import json
import os

import requests


def scrape_web_page(
    url: str,
    content_type: str | None = None,
    headers: str | None = None,
):
    # API endpoint (Flask scrape blueprint)
    api_url = "http://api/scrape"

    api_key = os.environ.get("MCP_API_KEY")

    req_headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: dict = {"url": url}
    if content_type is not None:
        payload["contentType"] = content_type
    if headers is not None:
        payload["headers"] = headers

    print(json.dumps(payload, indent=4, ensure_ascii=False))

    try:
        # Mercury parsing can be slow; use a generous client timeout
        response = requests.post(api_url, headers=req_headers, json=payload, timeout=120)
        response.raise_for_status()

        result = response.json()
        print("Scrape succeeded; response:")
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
    scrape_web_page("https://blog.pulipuli.info/")
