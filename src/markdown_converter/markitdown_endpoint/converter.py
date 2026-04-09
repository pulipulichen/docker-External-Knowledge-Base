import hashlib
import logging
import os
import threading

import redis
from markitdown import MarkItDown

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

_md_instance = None

IMAGE_DESCRIPTION_ENABLED = os.environ.get("IMAGE_DESCRIPTION_ENABLED", "false")

REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "0"))
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", "2592000"))

_convert_cache_redis: redis.StrictRedis | None = None
_convert_cache_redis_failed = False
_convert_cache_redis_lock = threading.Lock()

from .process_image_description import process_image_description


def get_markitdown():
    """Lazy-init MarkItDown in the current worker process."""
    global _md_instance
    if _md_instance is None:
        _md_instance = MarkItDown()
    return _md_instance


def _get_convert_cache_redis() -> redis.StrictRedis | None:
    global _convert_cache_redis, _convert_cache_redis_failed
    if _convert_cache_redis_failed:
        return None
    if _convert_cache_redis is not None:
        return _convert_cache_redis
    with _convert_cache_redis_lock:
        if _convert_cache_redis_failed:
            return None
        if _convert_cache_redis is not None:
            return _convert_cache_redis
        try:
            client = redis.StrictRedis(
                host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True
            )
            client.ping()
            _convert_cache_redis = client
            return client
        except redis.exceptions.RedisError as e:
            logger.error("MarkItDown cache: Redis unavailable (%s); caching disabled.", e)
            _convert_cache_redis_failed = True
            return None


def _sha256_file(file_path: str, chunk_size: int = 1024 * 1024) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _pipeline_fingerprint() -> str:
    """Parts of the post-convert pipeline that affect the returned string."""
    parts = [IMAGE_DESCRIPTION_ENABLED]
    if IMAGE_DESCRIPTION_ENABLED == "true":
        parts.append(os.environ.get("GEMINI_MODEL", ""))
        parts.append(os.environ.get("IMAGE_DESCRIBE_MIN_EDGE_PX", "128"))
    return "\0".join(parts)


def _convert_cache_key(file_path: str) -> str | None:
    try:
        st = os.stat(file_path)
    except OSError:
        return None
    abs_path = os.path.abspath(file_path)
    mtime_ns = getattr(st, "st_mtime_ns", int(st.st_mtime * 1_000_000_000))
    content_sha = _sha256_file(file_path)
    payload = (
        f"{abs_path}\0{mtime_ns}\0{content_sha}\0{_pipeline_fingerprint()}".encode("utf-8")
    )
    digest = hashlib.sha256(payload).hexdigest()
    return f"markitdown:convert:{digest}"


def convert_path_to_markdown(file_path: str) -> str:
    """Run MarkItDown on a local file path; returns extracted markdown text."""
    cache_key = _convert_cache_key(file_path)
    r = _get_convert_cache_redis()
    if r is not None and cache_key is not None:
        try:
            cached = r.get(cache_key)
            if cached is not None:
                logger.info("Conversion cache hit: %s", file_path)
                return cached
        except redis.exceptions.RedisError as e:
            logger.warning("Conversion cache get failed: %s", e)

    md = get_markitdown()

    logger.info("Conversion is starting: %s", file_path)

    markdown_content = md.convert(file_path, keep_data_uris=True).text_content

    logger.info("Conversion is successful: %s", file_path)

    if IMAGE_DESCRIPTION_ENABLED == "true":
        markdown_content = process_image_description(markdown_content)

    if r is not None and cache_key is not None:
        try:
            r.setex(cache_key, CACHE_EXPIRATION_SECONDS, markdown_content)
        except redis.exceptions.RedisError as e:
            logger.warning("Conversion cache set failed: %s", e)

    return markdown_content
