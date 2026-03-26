import asyncio
import logging
import os

import requests
from flask import Blueprint, Flask, jsonify, request

from ..auth.check_auth import check_auth  # Import check_auth from the new auth module

scrape_bp = Blueprint('scrape', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)  # Keep a dummy app for local testing if __name__ == '__main__'

USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"

MERCURY_PARSER_URL = os.getenv("MERCURY_PARSER_URL", "http://mercury-parser:3000").rstrip("/")
MERCURY_REQUEST_TIMEOUT = int(os.getenv("MERCURY_REQUEST_TIMEOUT", "90"))


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

    content_type = data.get("contentType")
    if content_type is not None and not isinstance(content_type, str):
        return jsonify({"error": "Field 'contentType' must be a string"}), 400

    headers_param = data.get("headers")
    if headers_param is not None and not isinstance(headers_param, str):
        return jsonify({
            "error": "Field 'headers' must be a URL-encoded string (see mercury-parser API docs)",
        }), 400

    try:
        status, results = await asyncio.to_thread(
            _call_mercury_parser,
            target_url,
            content_type,
            headers_param,
        )
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
