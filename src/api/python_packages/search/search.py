import asyncio
import logging
import os
import yaml

import requests
from flask import Blueprint, Flask, jsonify, request

from ..auth.check_auth import check_auth  # Import check_auth from the new auth module
from ..google_news_url import resolve_google_news_article_url
from ..scrape.scrape import (
    _call_mercury_parser,
    _scrape_cache_get,
    _scrape_cache_set,
)

search_bp = Blueprint('search', __name__)

logger = logging.getLogger(__name__)
# Configure logging
logging.basicConfig(level=logging.DEBUG)
app = Flask(__name__)  # Keep a dummy app for local testing if __name__ == '__main__'

SEARXNG_URL = os.getenv("SEARXNG_URL", "http://searxng:8080").rstrip("/")
SEARXNG_REQUEST_TIMEOUT = int(os.getenv("SEARXNG_REQUEST_TIMEOUT", "30"))
DEFAULT_SEARCH_RESULT_LIMIT = 5
MAX_SEARCH_RESULT_LIMIT = int(os.getenv("SEARCH_MAX_RESULT_LIMIT", "50"))

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

# 一次只允許一個查詢進行（跨所有 worker/請求共享於同一個 Python process）
_SEARCH_LOCK = asyncio.Lock()

# SearXNG 每筆結果只對外保留的欄位
_SEARXNG_RESULT_KEYS = ("content", "publishedDate", "score", "title", "url")


def _omit_searxng_field_value(v) -> bool:
    """值為 null、False 或空字串時不輸出該鍵（數字 0 仍會輸出）。"""
    if v is None or v is False:
        return True
    return v == ""


def _trim_searxng_result_items(body: dict, limit: int) -> dict:
    """從 SearXNG JSON 回應中，將 results 內每筆只保留指定欄位；略過 null / False / 空字串的鍵。其餘頂層鍵不變。"""
    raw = body.get("results")
    if not isinstance(raw, list):
        return body
    trimmed = []
    for item in raw[:limit]:
        if isinstance(item, dict):
            out_item = {}
            for k in _SEARXNG_RESULT_KEYS:
                v = item.get(k)
                if not _omit_searxng_field_value(v):
                    out_item[k] = v
            trimmed.append(out_item)
        else:
            trimmed.append(item)
    out = dict(body)
    out["results"] = trimmed
    return out


def _searxng_results_list_only(body) -> list:
    """成功時只對外回傳 SearXNG 的 results 陣列；其餘頂層鍵不帶出。"""
    if isinstance(body, dict):
        items = body.get("results")
        return items if isinstance(items, list) else []
    return []


def _client_ip_from_request(req) -> str | None:
    """Upstream reverse proxy 常見會帶 X-Forwarded-For / X-Real-IP；否則用 Flask 看到的 remote_addr。"""
    xff = req.headers.get("X-Forwarded-For")
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    xri = req.headers.get("X-Real-IP")
    if xri:
        s = xri.strip()
        if s:
            return s
    ra = req.remote_addr
    return ra if ra else None


def _call_searxng(
    query: str,
    categories: str | None,
    language: str | None,
    pageno: int,
    safesearch: int | None,
    time_range: str | None,
    client_ip: str | None = None,
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

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    logger.info(f"searxng endpoint: {endpoint}")
    logger.info(f"searxng params: {params}")

    # limiter.toml 將 Docker 網段視為 trusted proxy 時，SearXNG 要求一定要有這兩個 header
    # effective_ip = client_ip or "127.0.0.1"
    # headers["X-Real-IP"] = effective_ip
    # headers["X-Forwarded-For"] = effective_ip
    
    # resp = requests.get(endpoint, params=params, headers=headers, timeout=SEARXNG_REQUEST_TIMEOUT)
    resp = requests.get(endpoint, params=params, headers=headers, timeout=SEARXNG_REQUEST_TIMEOUT)
    try:
        body = resp.json()
        logger.info(f"searxng body: {body}")
    except ValueError:
        body = {
            "error": "searxng returned non-JSON body",
            "detail": (resp.text or "")[:500],
        }
    return resp.status_code, body


def _enrich_searxng_results_fulltext(body: dict) -> None:
    """
    對 results 內每筆以 url 經 Mercury 取全文；有全文時寫入 content，否則不帶 content 欄位（與 /scrape 相同快取）。
    原先 SearXNG 的摘要欄 content 先複製到 snippet 再覆寫或移除 content。
    """
    raw = body.get("results")
    if not isinstance(raw, list):
        return
    content_type = "markdown"
    headers_param = None
    for item in raw:
        if not isinstance(item, dict):
            continue
        if "content" in item:
            item["snippet"] = item["content"]
        url = item.get("url")
        if not url or not isinstance(url, str):
            item.pop("content", None)
            continue
        cached = _scrape_cache_get(url, content_type, headers_param)
        if cached is not None:
            content = cached.get("content")
            if content is not None and len(content.strip()) > 0:
                item["content"] = content.strip()
            else:
                item.pop("content", None)
            continue
        resolved = resolve_google_news_article_url(url)
        status, mercury_body = _call_mercury_parser(
            resolved, content_type, headers_param
        )
        if status == 200:
            _scrape_cache_set(url, content_type, headers_param, mercury_body)
            content = mercury_body.get("content")
            if content is not None and len(content.strip()) > 0:
                item["content"] = content.strip()
            else:
                item.pop("content", None)
        else:
            item.pop("content", None)


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

    safesearch = data.get("safesearch", 1)
    if safesearch is not None and safesearch not in (0, 1, 2):
        return jsonify({"error": "Field 'safesearch' must be 0, 1, or 2 if provided"}), 400

    time_range = data.get("time_range")
    if time_range is not None and not isinstance(time_range, str):
        return jsonify({"error": "Field 'time_range' must be a string"}), 400

    fulltext = data.get("fulltext", True)
    if not isinstance(fulltext, bool):
        return (
            jsonify({"error": "Field 'fulltext' must be a boolean if provided"}),
            400,
        )

    limit_raw = data.get("limit", DEFAULT_SEARCH_RESULT_LIMIT)
    if isinstance(limit_raw, bool):
        return (
            jsonify({"error": "Field 'limit' must be an integer if provided"}),
            400,
        )
    if not isinstance(limit_raw, int):
        return (
            jsonify({"error": "Field 'limit' must be an integer if provided"}),
            400,
        )
    if limit_raw < 1 or limit_raw > MAX_SEARCH_RESULT_LIMIT:
        return (
            jsonify(
                {
                    "error": (
                        f"Field 'limit' must be between 1 and {MAX_SEARCH_RESULT_LIMIT}"
                    ),
                }
            ),
            400,
        )
    limit = limit_raw

    client_ip = _client_ip_from_request(request)

    async with _SEARCH_LOCK:
        response = None
        status_code = None
        try:
            status, results = await asyncio.to_thread(
                _call_searxng,
                query,
                categories,
                language,
                pageno,
                safesearch,
                time_range,
                client_ip,
            )
        except requests.exceptions.Timeout:
            response = jsonify({"error": "searxng request timed out"})
            status_code = 504
        except requests.exceptions.RequestException as e:
            logging.exception("searxng request failed")
            response = jsonify({"error": "Failed to reach searxng", "detail": str(e)})
            status_code = 502
        else:
            if results is None:
                response = jsonify({"error": "searxng returned None"})
                status_code = 500
            elif status != 200:
                logging.exception("other fails:" + str(results))
                response = jsonify(results)
                status_code = status
            else:
                if isinstance(results, dict):
                    results = _trim_searxng_result_items(results, limit)
                if fulltext and isinstance(results, dict):
                    try:
                        await asyncio.to_thread(
                            _enrich_searxng_results_fulltext, results
                        )
                    except requests.exceptions.Timeout:
                        response = jsonify(
                            {
                                "error": "Full article fetch (mercury-parser) timed out",
                            }
                        )
                        status_code = 504
                    except requests.exceptions.RequestException as e:
                        logging.exception("Search fulltext scrape failed")
                        response = jsonify(
                            {
                                "error": "Failed to fetch full article text",
                                "detail": str(e),
                            }
                        )
                        status_code = 502
                    else:
                        response = jsonify(_searxng_results_list_only(results))
                        status_code = 200
                else:
                    response = jsonify(_searxng_results_list_only(results))
                    status_code = 200

        # 每個查詢結束後等待 1 秒鐘才回傳
        await asyncio.sleep(1)
        return response, status_code

if __name__ == '__main__':
    # This block is for local testing of the retrieval blueprint
    # In a real application, this blueprint would be registered with a main app
    app.register_blueprint(search_bp)
    app.run(host="0.0.0.0", port=80, debug=True)
