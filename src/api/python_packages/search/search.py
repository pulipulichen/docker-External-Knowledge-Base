import asyncio
import logging
import os
import yaml

import requests
from flask import Blueprint, Flask, jsonify, request

from ..auth.check_auth import check_auth  # Import check_auth from the new auth module

search_bp = Blueprint('search', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)  # Keep a dummy app for local testing if __name__ == '__main__'

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080").rstrip("/")
SEARXNG_REQUEST_TIMEOUT = int(os.getenv("SEARXNG_REQUEST_TIMEOUT", "30"))

# --- Load SearXNG Secret Key ---
SEARXNG_SETTINGS_PATH = os.getenv("SEARXNG_SETTINGS_PATH", "/etc/searxng/settings.yml")
SEARXNG_SECRET: str = os.getenv("SEARXNG_SECRET") or ""

if not SEARXNG_SECRET and os.path.exists(SEARXNG_SETTINGS_PATH):
    try:
        with open(SEARXNG_SETTINGS_PATH, "r") as f:
            _settings = yaml.safe_load(f)
            SEARXNG_SECRET = _settings.get("server", {}).get("secret_key")
            logging.debug(f"Loaded secret_key from {SEARXNG_SETTINGS_PATH}")
    except Exception as _e:
        logging.error(f"Failed to read SearXNG settings from {SEARXNG_SETTINGS_PATH}: {_e}")

if not SEARXNG_SECRET:
    # Fallback to default if everything else fails
    SEARXNG_SECRET = "ultrasecretkey2ultrasecretkey"


def _call_searxng(
    query: str,
    categories: str | None,
    language: str | None,
    pageno: int,
    safesearch: int | None,
    time_range: str | None,
) -> tuple[int, dict]:
    """Call SearXNG JSON API synchronously (for use with asyncio.to_thread)."""
    endpoint = f"{SEARXNG_URL}/search"
    params: dict[str, str] = {
        "q": query,
        "format": "json",
        "secret_key": SEARXNG_SECRET
    }
    if pageno:
        params["pageno"] = str(pageno)

    if categories:
        params["categories"] = categories
    if language:
        params["language"] = language
    if safesearch is not None:
        params["safesearch"] = str(safesearch)
    if time_range:
        params["time_range"] = time_range

    resp = requests.get(endpoint, params=params, timeout=SEARXNG_REQUEST_TIMEOUT)
    try:
        body = resp.json()
    except ValueError:
        body = {
            "error": "searxng returned non-JSON body",
            "detail": (resp.text or "")[:500],
        }
    return resp.status_code, body


@search_bp.route('/search', methods=['POST'])
async def search_endpoint():
    # Validate Bearer Token
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    # Read JSON body
    data = request.get_json(force=True)

    query = data.get("query")
    if not query or not isinstance(query, str):
        return jsonify({"error": "JSON body must include a string field 'query'"}), 400

    categories = data.get("categories")
    if categories is not None and not isinstance(categories, str):
        return jsonify({"error": "Field 'categories' must be a string"}), 400

    language = data.get("language")
    if language is not None and not isinstance(language, str):
        return jsonify({"error": "Field 'language' must be a string"}), 400

    pageno = data.get("pageno", 1)
    if not isinstance(pageno, int) or pageno < 1:
        return jsonify({"error": "Field 'pageno' must be a positive integer"}), 400

    safesearch = data.get("safesearch")
    if safesearch is not None and safesearch not in (0, 1, 2):
        return jsonify({"error": "Field 'safesearch' must be 0, 1, or 2 if provided"}), 400

    time_range = data.get("time_range")
    if time_range is not None and not isinstance(time_range, str):
        return jsonify({"error": "Field 'time_range' must be a string"}), 400

    try:
        status, results = await asyncio.to_thread(
            _call_searxng,
            query,
            categories,
            language,
            pageno,
            safesearch,
            time_range,
        )
    except requests.exceptions.Timeout:
        return jsonify({"error": "searxng request timed out"}), 504
    except requests.exceptions.RequestException as e:
        logging.exception("searxng request failed")
        return jsonify({"error": "Failed to reach searxng", "detail": str(e)}), 502

    if status != 200:
        return jsonify(results), status

    return jsonify(results)

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(search_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
