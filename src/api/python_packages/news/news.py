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


def _news_cache_set(q: str, h: str, g: str, c: str, markdown: str) -> None:
    r = _get_news_redis()
    if not r:
        return
    key = _news_redis_cache_key(q, h, g, c)
    try:
        r.setex(key, NEWS_CACHE_TTL_SECONDS, markdown)
    except redis.exceptions.RedisError as e:
        logger.warning("News cache set failed: %s", e)


def _strip_html(text: str | None) -> str:
    if not text:
        return ""
    t = re.sub(r"<[^>]+>", " ", text)
    t = html.unescape(t)
    return " ".join(t.split())


def _rss_to_markdown(xml_bytes: bytes) -> str:
    root = ET.fromstring(xml_bytes)
    channel = root.find("channel")
    if channel is None:
        return ""

    ch_title = (channel.findtext("title") or "").strip()
    ch_link = (channel.findtext("link") or "").strip()
    lines: list[str] = []

    if ch_title:
        lines.append(f"# {ch_title}")
    if ch_link:
        lines.append(f"")
        lines.append(f"來源：<{ch_link}>")
    lines.append("")
    lines.append("---")
    lines.append("")

    items = channel.findall("item")
    for i, item in enumerate(items, start=1):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub = (item.findtext("pubDate") or "").strip()
        desc = _strip_html(item.findtext("description"))

        lines.append(f"## {i}. {title or '(無標題)'}")
        if link:
            lines.append(f"- [閱讀全文]({link})")
        if pub:
            lines.append(f"- 發布時間：{pub}")
        if desc:
            lines.append(f"- 摘要：{desc}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _fetch_google_news_rss(
    query: str,
    hl: str,
    gl: str,
    ceid: str,
    client_ip: str | None,
) -> tuple[int, str]:
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
        md = _rss_to_markdown(resp.content)
    except ET.ParseError as e:
        return 502, f"無法解析 RSS：{e}"

    return 200, md


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

    cached_md = _news_cache_get(q, h, g, c)
    if cached_md is not None:
        return jsonify({"markdown": cached_md, "cached": True})

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

    _news_cache_set(q, h, g, c, payload)
    return jsonify({"markdown": payload, "cached": False})
