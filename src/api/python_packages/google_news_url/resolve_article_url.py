"""將 news.google.com 文章包裝網址解成發布者原文 URL（例如供 RSS / Mercury 使用）。"""

from __future__ import annotations

import hashlib
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from urllib.parse import urlparse

import redis
from googlenewsdecoder import gnewsdecoder

GNEWS_RESOLVE_TIMEOUT_SECONDS = float(os.getenv("GNEWS_RESOLVE_TIMEOUT_SECONDS", "10"))
GNEWS_URL_CACHE_TTL_SECONDS = int(
    os.getenv("GNEWS_URL_CACHE_TTL_SECONDS", str(24 * 3600))
)

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))

_gnews_url_redis: redis.StrictRedis | None = None
_gnews_url_redis_failed = False
_gnews_url_redis_lock = threading.Lock()

_decode_executor = ThreadPoolExecutor(
    max_workers=int(os.getenv("GNEWS_RESOLVE_MAX_WORKERS", "8")),
    thread_name_prefix="gnews_resolve",
)


def _get_gnews_url_redis() -> redis.StrictRedis | None:
    global _gnews_url_redis, _gnews_url_redis_failed
    if _gnews_url_redis_failed:
        return None
    if _gnews_url_redis is not None:
        return _gnews_url_redis
    with _gnews_url_redis_lock:
        if _gnews_url_redis_failed:
            return None
        if _gnews_url_redis is not None:
            return _gnews_url_redis
        try:
            client = redis.StrictRedis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
            )
            client.ping()
            _gnews_url_redis = client
            return client
        except redis.exceptions.RedisError as e:
            logging.error(
                "Google News URL cache: Redis unavailable (%s); caching disabled.", e
            )
            _gnews_url_redis_failed = True
            return None


def _gnews_url_cache_key(url: str) -> str:
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return f"gnews:article:url:{digest}"


def _cache_get_resolved(url: str) -> str | None:
    r = _get_gnews_url_redis()
    if not r:
        return None
    try:
        return r.get(_gnews_url_cache_key(url))
    except redis.exceptions.RedisError as e:
        logging.warning("Google News URL cache get failed: %s", e)
        return None


def _cache_set_resolved(url: str, resolved: str) -> None:
    r = _get_gnews_url_redis()
    if not r:
        return
    try:
        r.setex(_gnews_url_cache_key(url), GNEWS_URL_CACHE_TTL_SECONDS, resolved)
    except redis.exceptions.RedisError as e:
        logging.warning("Google News URL cache set failed: %s", e)


def _decode_in_thread(url: str) -> str:
    try:
        out = gnewsdecoder(url, interval=0)
        if out.get("status") and isinstance(out.get("decoded_url"), str):
            return out["decoded_url"]
        logging.warning("Google News decode failed for url: %s — %s", url, out)
    except Exception:
        logging.exception("Google News decode raised for url: %s", url)
    return url


def resolve_google_news_article_url(url: str) -> str:
    host = (urlparse(url).hostname or "").lower()
    if host != "news.google.com":
        return url

    cached = _cache_get_resolved(url)
    if cached is not None:
        return cached

    fut = _decode_executor.submit(_decode_in_thread, url)
    try:
        resolved = fut.result(timeout=GNEWS_RESOLVE_TIMEOUT_SECONDS)
    except FuturesTimeoutError:
        logging.warning(
            "Google News decode timed out (%.2fs) for url: %s",
            GNEWS_RESOLVE_TIMEOUT_SECONDS,
            url,
        )
        return url

    if resolved != url:
        _cache_set_resolved(url, resolved)
    return resolved
