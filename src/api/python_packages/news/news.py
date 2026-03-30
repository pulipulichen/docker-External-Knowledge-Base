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
from ..search.search import _client_ip_from_request

news_bp = Blueprint("news", __name__)

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS_BASE = "https://news.google.com/rss/search"
NEWS_REQUEST_TIMEOUT = int(os.getenv("NEWS_REQUEST_TIMEOUT", "30"))
NEWS_CACHE_TTL_SECONDS = int(os.getenv("NEWS_CACHE_TTL_SECONDS", str(24 * 3600)))

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


def _news_redis_cache_key(q: str, h: str, g: str, c: str) -> str:
    payload = json.dumps([q, h, g, c], ensure_ascii=False, separators=(",", ":"))
    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    return f"news:rss:{digest}"


def _news_cache_get(q: str, h: str, g: str, c: str) -> str | None:
    r = _get_news_redis()
    if not r:
        return None
    key = _news_redis_cache_key(q, h, g, c)
    try:
        return r.get(key)
    except redis.exceptions.RedisError as e:
        logger.warning("News cache get failed: %s", e)
        return None


def _news_cache_set(q: str, h: str, g: str, c: str, payload_json: str) -> None:
    r = _get_news_redis()
    if not r:
        return
    key = _news_redis_cache_key(q, h, g, c)
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
        for t in ("title", "link", "pubDate"):
            el = item.find(t)
            if el is not None and el.text is not None:
                entry[t] = el.text.strip()
        if "link" in entry:
            entry["link"] = resolve_google_news_article_url(entry["link"])
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

    resp = requests.get(
        GOOGLE_NEWS_RSS_BASE,
        params=params,
        headers=headers,
        timeout=NEWS_REQUEST_TIMEOUT,
    )
    if resp.status_code != 200:
        return resp.status_code, (resp.text or "")[:2000]

    ct = (resp.headers.get("Content-Type") or "").lower()
    if "xml" not in ct and not (resp.content or b"").lstrip().startswith(b"<?xml"):
        return 502, "Google News 回應不是有效的 RSS/XML"

    try:
        payload = _parse_rss_items(resp.content)
    except ET.ParseError as e:
        return 502, f"無法解析 RSS：{e}"

    return 200, payload


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

    cached_raw = _news_cache_get(q, h, g, c)
    if cached_raw is not None:
        try:
            body = json.loads(cached_raw)
            if isinstance(body, list):
                return jsonify(body)
        except json.JSONDecodeError:
            pass

    client_ip = _client_ip_from_request(request)

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
        return jsonify({"error": "Google News RSS request timed out"}), 504
    except requests.exceptions.RequestException as e:
        logging.exception("Google News RSS request failed")
        return jsonify({"error": "Failed to reach Google News RSS", "detail": str(e)}), 502

    if status != 200:
        return jsonify({"error": "Google News RSS error", "detail": payload}), status

    assert isinstance(payload, list)
    cache_str = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
    _news_cache_set(q, h, g, c, cache_str)

    return jsonify(payload)
