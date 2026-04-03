import asyncio
import hashlib
import json
import logging
import os
import threading

import redis
import requests
from flask import Blueprint, Flask, jsonify, request

from ..auth.check_auth import check_auth  # Import check_auth from the new auth module
from ..google_news_url import resolve_google_news_article_url

scrape_bp = Blueprint('scrape', __name__)

# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)  # Keep a dummy app for local testing if __name__ == '__main__'

USE_MOCK_DB = os.getenv("USE_MOCK_DB", "true").lower() == "true"

MERCURY_PARSER_URL = os.getenv("MERCURY_PARSER_URL", "http://mercury-parser:3000").rstrip("/")
MERCURY_REQUEST_TIMEOUT = int(os.getenv("MERCURY_REQUEST_TIMEOUT", "90"))

SCRAPE_CACHE_TTL_SECONDS = int(os.getenv("SCRAPE_CACHE_TTL_SECONDS", str(24 * 3600)))
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

_scrape_redis: redis.StrictRedis | None = None
_scrape_redis_failed = False
_scrape_redis_lock = threading.Lock()


def _get_scrape_redis() -> redis.StrictRedis | None:
    global _scrape_redis, _scrape_redis_failed
    if _scrape_redis_failed:
        return None
    if _scrape_redis is not None:
        return _scrape_redis
    with _scrape_redis_lock:
        if _scrape_redis_failed:
            return None
        if _scrape_redis is not None:
            return _scrape_redis
        try:
            client = redis.StrictRedis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
            )
            client.ping()
            _scrape_redis = client
            return client
        except redis.exceptions.RedisError as e:
            logging.error("Scrape cache: Redis unavailable (%s); caching disabled.", e)
            _scrape_redis_failed = True
            return None


def _scrape_cache_key(url: str, content_type: str | None, headers: str | None) -> str:
    """以查詢網址為主體，並納入會影響 Mercury 結果的參數。"""
    ct = content_type if content_type is not None else "markdown"
    hp = headers if headers is not None else ""
    payload = json.dumps([url, ct, hp], ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"scrape:mercury:{digest}"


def _scrape_cache_get(url: str, content_type: str | None, headers: str | None) -> dict | None:
    r = _get_scrape_redis()
    if not r:
        return None
    key = _scrape_cache_key(url, content_type, headers)
    try:
        raw = r.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except (redis.exceptions.RedisError, json.JSONDecodeError) as e:
        logging.warning("Scrape cache get failed: %s", e)
        return None


def _scrape_cache_set(url: str, content_type: str | None, headers: str | None, body: dict) -> None:
    r = _get_scrape_redis()
    if not r:
        return
    key = _scrape_cache_key(url, content_type, headers)
    try:
        r.setex(key, SCRAPE_CACHE_TTL_SECONDS, json.dumps(body, ensure_ascii=False))
    except (redis.exceptions.RedisError, TypeError) as e:
        logging.warning("Scrape cache set failed: %s", e)


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

    if resp.status_code == 200 and isinstance(body, dict):
        raw = body.get("content")
        if isinstance(raw, str):
            stripped = raw.strip()
        elif raw is None:
            stripped = ""
        else:
            stripped = None
        if stripped is not None:
            body = {**body, "content": stripped}
            if len(stripped) < 10:
                return 422, {
                    "error": "mercury-parser content too short after strip",
                    "detail": f"content length is {len(stripped)}, minimum is 10",
                }

    logging.info("scrape body: %s", body)

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

    cached = _scrape_cache_get(target_url, content_type, headers_param)
    if cached is not None:
        return jsonify(cached)

    def _scrape_with_resolved_url() -> tuple[int, dict]:
        resolved = resolve_google_news_article_url(target_url)
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

    _scrape_cache_set(target_url, content_type, headers_param, results)
    return jsonify(results)

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(scrape_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
