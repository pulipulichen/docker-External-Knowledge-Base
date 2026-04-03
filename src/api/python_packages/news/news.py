import asyncio
import hashlib
import html
import json
import logging
import os
import re
import threading
import xml.etree.ElementTree as ET

import redis
import requests
from flask import Blueprint, jsonify, request

from ..auth.check_auth import check_auth
from ..google_news_url import resolve_google_news_article_url
from ..scrape.scrape import (
    _call_mercury_parser,
    _scrape_cache_get,
    _scrape_cache_set,
)
from ..search.search import _client_ip_from_request

news_bp = Blueprint("news", __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search"
NEWS_REQUEST_TIMEOUT = int(os.getenv("NEWS_REQUEST_TIMEOUT", "30"))
NEWS_CACHE_TTL_SECONDS = int(os.getenv("NEWS_CACHE_TTL_SECONDS", str(24 * 3600)))
DEFAULT_NEWS_RESULT_LIMIT = 5
MAX_NEWS_RESULT_LIMIT = int(os.getenv("NEWS_MAX_RESULT_LIMIT", "50"))

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

_news_redis: redis.StrictRedis | None = None
_news_redis_failed = False
_news_redis_lock = threading.Lock()


def _get_news_redis() -> redis.StrictRedis | None:
    """延遲連線：只在實際需要快取時連 Redis（由 Docker 內的 API 進程在處理請求時建立）。"""
    global _news_redis, _news_redis_failed
    if _news_redis_failed:
        return None
    if _news_redis is not None:
        return _news_redis
    with _news_redis_lock:
        if _news_redis_failed:
            return None
        if _news_redis is not None:
            return _news_redis
        try:
            client = redis.StrictRedis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
            )
            client.ping()
            _news_redis = client
            return client
        except redis.exceptions.RedisError as e:
            logger.error("News cache: Redis unavailable (%s); caching disabled.", e)
            _news_redis_failed = True
            return None

DEFAULT_HL = "zh-TW"
DEFAULT_GL = "TW"
DEFAULT_CEID = "TW:zh-Hant"

# 一次只允許一個 /news 查詢進行（同一 Python process 內）
_NEWS_LOCK = asyncio.Lock()


def _news_redis_cache_key(
    q: str, h: str, g: str, c: str, fulltext: bool, limit: int
) -> str:
    payload = json.dumps(
        [q, h, g, c, fulltext, limit], ensure_ascii=False, separators=(",", ":")
    )
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"news:rss:{digest}"


def _news_cache_get(
    q: str, h: str, g: str, c: str, fulltext: bool, limit: int
) -> str | None:
    r = _get_news_redis()
    if not r:
        return None
    key = _news_redis_cache_key(q, h, g, c, fulltext, limit)
    try:
        return r.get(key)
    except redis.exceptions.RedisError as e:
        logger.warning("News cache get failed: %s", e)
        return None


def _news_cache_set(
    q: str, h: str, g: str, c: str, fulltext: bool, limit: int, payload_json: str
) -> None:
    r = _get_news_redis()
    if not r:
        return
    key = _news_redis_cache_key(q, h, g, c, fulltext, limit)
    try:
        r.setex(key, NEWS_CACHE_TTL_SECONDS, payload_json)
    except redis.exceptions.RedisError as e:
        logger.warning("News cache set failed: %s", e)


def _unwrap_anchor_tags(s: str) -> str:
    """移除 <a>…</a>，只保留內文（可巢狀多次）。"""
    prev = None
    while prev != s:
        prev = s
        s = re.sub(
            r"<a\b[^>]*>(.*?)</a>",
            r"\1",
            s,
            count=1,
            flags=re.DOTALL | re.IGNORECASE,
        )
    return s


def _remove_urls_from_text(s: str) -> str:
    return re.sub(r"https?://\S+", "", s)


def _li_inner_to_plain(fragment: str) -> str:
    fragment = re.sub(
        r"<font\b[^>]*>(.*?)</font>",
        r" \1 ",
        fragment,
        flags=re.DOTALL | re.IGNORECASE,
    )
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment)
    return " ".join(fragment.split())


def _description_html_to_markdown_no_links(raw: str | None) -> str:
    """
    Google News 的 <description> 常為 HTML（如 ol/li + a + font）。
    轉成 Markdown 編號列表，並移除所有超連結（含裸 URL）。
    """
    if not raw:
        return ""
    s = html.unescape(raw)
    s = _unwrap_anchor_tags(s)
    s = _remove_urls_from_text(s)

    lines: list[str] = []
    for m in re.finditer(r"<li\b[^>]*>(.*?)</li>", s, re.DOTALL | re.IGNORECASE):
        line = _li_inner_to_plain(m.group(1))
        if line:
            lines.append(line)

    if lines:
        return "\n".join(f"{i}. {t}" for i, t in enumerate(lines, start=1))

    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = _remove_urls_from_text(s)
    s = " ".join(s.split())
    return s


def _parse_rss_items(xml_bytes: bytes) -> list[dict]:
    """解析 RSS 2.0，回傳 item 陣列（不含 guid）。"""
    root = ET.fromstring(xml_bytes)
    channel_el = root.find("channel")
    if channel_el is None:
        return []

    items_out: list[dict] = []
    for item in channel_el.findall("item"):
        entry: dict = {}
        for tag in ("title", "pubDate"):
            el = item.find(tag)
            if el is not None and el.text is not None:
                entry[tag] = el.text.strip()
        link_el = item.find("link")
        if link_el is not None and link_el.text:
            entry["url"] = link_el.text.strip()
        items_out.append(entry)

    return items_out


def _fetch_google_news_rss(
    query: str,
    hl: str,
    gl: str,
    ceid: str,
    client_ip: str | None,
) -> tuple[int, list[dict] | str]:
    params = {"q": query, "hl": hl, "gl": gl, "ceid": ceid}
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
        "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
    }
    effective_ip = client_ip or "127.0.0.1"
    headers["X-Real-IP"] = effective_ip
    headers["X-Forwarded-For"] = effective_ip

    # logging.info(
    #     "Before Google News RSS request: Query: %s, HL: %s, GL: %s, CEID: %s",
    #     query,
    #     hl,
    #     gl,
    #     ceid,
    # )

    resp = requests.get(
        GOOGLE_NEWS_RSS_BASE,
        params=params,
        headers=headers,
        timeout=NEWS_REQUEST_TIMEOUT,
    )

    # logging.info("1 After Google News RSS request: %s", resp.status_code)

    if resp.status_code != 200:
        return resp.status_code, (resp.text or "")[:2000]

    # logging.info("2 After Google News RSS request: %s", resp.status_code)

    ct = (resp.headers.get("Content-Type") or "").lower()
    if "xml" not in ct and not (resp.content or b"").lstrip().startswith(b"<?xml"):
        return 502, "Google News 回應不是有效的 RSS/XML"

    # logging.info("3 After Google News RSS request: %s", resp.status_code)

    try:
        payload = _parse_rss_items(resp.content)
    except ET.ParseError as e:
        return 502, f"無法解析 RSS：{e}"
    except Exception as e:
        return 502, f"發生無法處理的錯誤：{e}"

    # logging.info("4 After Google News RSS request: %s", resp.status_code)

    return 200, payload


def _enrich_items_fulltext(items: list[dict]) -> None:
    """以 RSS <link> 解析出的 url 經 Mercury 取全文；有全文時寫入 content，否則不帶 content 欄位（與 /scrape 相同快取鍵邏輯）。"""
    content_type = "markdown"
    headers_param = None
    for entry in items:
        item_url = entry.get("url")
        logging.info("item_url: %s", item_url)
        if not item_url:
            entry.pop("content", None)
            continue
        cached = _scrape_cache_get(item_url, content_type, headers_param)
        if cached is not None:
            content = cached.get("content")
            if content is not None and len(content.strip()) > 0:
                entry["content"] = content.strip()
            else:
                entry.pop("content", None)
            continue
        resolved = resolve_google_news_article_url(item_url)
        status, body = _call_mercury_parser(resolved, content_type, headers_param)
        if status == 200:
            _scrape_cache_set(item_url, content_type, headers_param, body)
            content = body.get("content")
            if content is not None and len(content.strip()) > 0:
                entry["content"] = content.strip()
            else:
                entry.pop("content", None)
        else:
            entry.pop("content", None)


@news_bp.route("/news", methods=["POST"])
async def news_endpoint():
    if not check_auth(request):
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json(force=True)

    query = data.get("query")
    if not query or not isinstance(query, str):
        return jsonify({"error": "JSON body must include a string field 'query'"}), 400

    hl = data.get("hl", DEFAULT_HL)
    gl = data.get("gl", DEFAULT_GL)
    ceid = data.get("ceid", DEFAULT_CEID)
    for name, val in (("hl", hl), ("gl", gl), ("ceid", ceid)):
        if not isinstance(val, str) or not val.strip():
            return jsonify({"error": f"Field '{name}' must be a non-empty string if provided"}), 400

    q, h, g, c = query.strip(), hl.strip(), gl.strip(), ceid.strip()

    fulltext = data.get("fulltext", True)
    if not isinstance(fulltext, bool):
        return (
            jsonify({"error": "Field 'fulltext' must be a boolean if provided"}),
            400,
        )

    disable_cache = data.get("disable_cache", False)
    if not isinstance(disable_cache, bool):
        return (
            jsonify({"error": "Field 'disable_cache' must be a boolean if provided"}),
            400,
        )

    limit_raw = data.get("limit", DEFAULT_NEWS_RESULT_LIMIT)
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
    if limit_raw < 1 or limit_raw > MAX_NEWS_RESULT_LIMIT:
        return (
            jsonify(
                {
                    "error": (
                        f"Field 'limit' must be between 1 and {MAX_NEWS_RESULT_LIMIT}"
                    ),
                }
            ),
            400,
        )
    limit = limit_raw

    client_ip = _client_ip_from_request(request)

    # logging.info(f"Query: {q}, HL: {h}, GL: {g}, CEID: {c}")

    async with _NEWS_LOCK:
        response = None
        status_code = None

        cached_raw = (
            None
            if disable_cache
            else _news_cache_get(q, h, g, c, fulltext, limit)
        )
        if cached_raw is not None:
            try:
                body = json.loads(cached_raw)
                if isinstance(body, list):
                    response = jsonify(body)
                    status_code = 200
            except json.JSONDecodeError:
                pass

        if response is None:
            try:
                status, payload = await asyncio.to_thread(
                    _fetch_google_news_rss,
                    q,
                    h,
                    g,
                    c,
                    client_ip,
                )
            except requests.exceptions.Timeout:
                response = jsonify({"error": "Google News RSS request timed out"})
                status_code = 504
            except requests.exceptions.RequestException as e:
                logging.exception("Google News RSS request failed")
                response = jsonify(
                    {"error": "Failed to reach Google News RSS", "detail": str(e)}
                )
                status_code = 502
            else:
                if status != 200:
                    response = jsonify({"error": "Google News RSS error", "detail": payload})
                    status_code = status
                else:
                    assert isinstance(payload, list)
                    payload = payload[:limit]
                    if fulltext:
                        try:
                            await asyncio.to_thread(_enrich_items_fulltext, payload)
                        except requests.exceptions.Timeout:
                            response = jsonify(
                                {"error": "Full article fetch (mercury-parser) timed out"}
                            )
                            status_code = 504
                        except requests.exceptions.RequestException as e:
                            logging.exception("News fulltext scrape failed")
                            response = jsonify(
                                {
                                    "error": "Failed to fetch full article text",
                                    "detail": str(e),
                                }
                            )
                            status_code = 502
                        else:
                            if not disable_cache:
                                cache_str = json.dumps(
                                    payload, ensure_ascii=False, separators=(",", ":")
                                )
                                _news_cache_set(q, h, g, c, fulltext, limit, cache_str)
                            response = jsonify(payload)
                            status_code = 200
                    else:
                        if not disable_cache:
                            cache_str = json.dumps(
                                payload, ensure_ascii=False, separators=(",", ":")
                            )
                            _news_cache_set(q, h, g, c, fulltext, limit, cache_str)
                        response = jsonify(payload)
                        status_code = 200

        await asyncio.sleep(1)
        return response, status_code
