import asyncio
import logging
import os
from urllib.parse import urlparse

import requests
from flask import Blueprint, Flask, jsonify, request
from googlenewsdecoder import gnewsdecoder

from ..auth.check_auth import check_auth  # Import check_auth from the new auth module

scrape_bp = Blueprint('scrape', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)  # Keep a dummy app for local testing if __name__ == '__main__'

USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"

MERCURY_PARSER_URL = os.getenv("MERCURY_PARSER_URL", "http://mercury-parser:3000").rstrip("/")
MERCURY_REQUEST_TIMEOUT = int(os.getenv("MERCURY_REQUEST_TIMEOUT", "90"))


def _resolve_google_news_article_url(url: str) -> str:
    """Turn news.google.com article wrapper URLs into the publisher URL (Mercury cannot follow JS redirects)."""
    host = (urlparse(url).hostname or "").lower()
    if host != "news.google.com":
        return url
    try:
        out = gnewsdecoder(url, interval=0)
        if out.get("status") and isinstance(out.get("decoded_url"), str):
            return out["decoded_url"]
        logging.warning("Google News decode failed for scrape url: %s — %s", url, out)
    except Exception:
        logging.exception("Google News decode raised for scrape url: %s", url)
    return url


def _call_mercury_parser(url: str, content_type: str | None, headers: str | None) -> tuple[int, dict]:
    """Call Mercury Parser API synchronously (for use with asyncio.to_thread)."""
    endpoint = f"{MERCURY_PARSER_URL}/parser"
    params = {"url": url}
    if content_type:
        params["contentType"] = content_type
    if headers:
        params["headers"] = headers

    resp = requests.get(endpoint, params=params, timeout=MERCURY_REQUEST_TIMEOUT)
    try:
        body = resp.json()
    except ValueError:
        body = {"error": "mercury-parser returned non-JSON body", "detail": (resp.text or "")[:500]}
    return resp.status_code, body


@scrape_bp.route('/scrape', methods=['POST'])
async def scrape_endpoint():
    # Validate Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Read JSON body
    data = request.get_json(force=True)

    target_url = data.get("url")
    if not target_url or not isinstance(target_url, str):
        return jsonify({"error": "JSON body must include a string field 'url'"}), 400

    content_type = data.get("contentType", "markdown")
    if content_type is not None and not isinstance(content_type, str):
        return jsonify({"error": "Field 'contentType' must be a string"}), 400

    headers_param = data.get("headers")
    if headers_param is not None and not isinstance(headers_param, str):
        return jsonify({
            "error": "Field 'headers' must be a URL-encoded string (see mercury-parser API docs)",
        }), 400

    def _scrape_with_resolved_url() -> tuple[int, dict]:
        resolved = _resolve_google_news_article_url(target_url)
        return _call_mercury_parser(resolved, content_type, headers_param)

    try:
        status, results = await asyncio.to_thread(_scrape_with_resolved_url)
    except requests.exceptions.Timeout:
        return jsonify({"error": "mercury-parser request timed out"}), 504
    except requests.exceptions.RequestException as e:
        logging.exception("mercury-parser request failed")
        return jsonify({"error": "Failed to reach mercury-parser", "detail": str(e)}), 502

    if status != 200:
        return jsonify(results), status

    return jsonify(results)

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(scrape_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
