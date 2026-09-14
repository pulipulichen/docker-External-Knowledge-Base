import asyncio
import httpx
import os
import redis
import json
import logging

from .wait_for_embedding_service import wait_for_embedding_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EMBEDDING_ENGINE = os.getenv("EMBEDDING_ENGINE", "ollama").strip().lower()
if EMBEDDING_ENGINE == "tei":
    logger.warning("EMBEDDING_ENGINE=tei is deprecated; using Ollama instead.")
    EMBEDDING_ENGINE = "ollama"

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434").rstrip("/")
OLLAMA_EMBEDDING_MODEL = os.getenv("OLLAMA_EMBEDDING_MODEL", "bge-m3").strip()
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", 3600))

GEMINI_EMBEDDING_BASE_URL = os.getenv(
    "GEMINI_EMBEDDING_BASE_URL",
    "https://generativelanguage.googleapis.com",
).rstrip("/")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2-preview")
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
GEMINI_TASK_QUERY = os.getenv("GEMINI_EMBEDDING_TASK_TYPE_QUERY", "RETRIEVAL_QUERY").strip()
GEMINI_TASK_DOCUMENT = os.getenv("GEMINI_EMBEDDING_TASK_TYPE_DOCUMENT", "RETRIEVAL_DOCUMENT").strip()
_GEMINI_OUT_DIM_RAW = os.getenv("GEMINI_EMBEDDING_OUTPUT_DIMENSIONALITY", "").strip()


def _embedding_model_cache_id() -> str:
    if EMBEDDING_ENGINE == "gemini":
        return GEMINI_EMBEDDING_MODEL
    return OLLAMA_EMBEDDING_MODEL


def _cache_key(text: str, for_query: bool) -> str:
    return f"embedding:{EMBEDDING_ENGINE}:{_embedding_model_cache_id()}:q={int(for_query)}:{text}"


def _gemini_uses_prompt_task_prefix(model: str) -> bool:
    m = model.lower()
    return "embedding-2" in m or "2-preview" in m


def _format_text_for_gemini(model: str, text: str, for_query: bool) -> str:
    if _gemini_uses_prompt_task_prefix(model):
        if for_query:
            return f"task: search result | query: {text}"
        return f"title: none | text: {text}"
    return text


def _parse_gemini_embedding_payload(data: dict):
    if not data:
        return None
    if "embedding" in data:
        emb = data["embedding"]
    elif data.get("embeddings"):
        emb = data["embeddings"][0]
    else:
        return None
    if isinstance(emb, dict) and "values" in emb:
        return emb["values"]
    return None


def _embedding_gemini_http(text: str, for_query: bool):
    if not GEMINI_API_KEY:
        logger.error("GEMINI_API_KEY is not set")
        return None

    model = GEMINI_EMBEDDING_MODEL
    url = f"{GEMINI_EMBEDDING_BASE_URL}/v1beta/models/{model}:embedContent"
    body_text = _format_text_for_gemini(model, text, for_query)
    payload = {"content": {"parts": [{"text": body_text}]}}
    if _GEMINI_OUT_DIM_RAW:
        payload["outputDimensionality"] = int(_GEMINI_OUT_DIM_RAW)
    if not _gemini_uses_prompt_task_prefix(model):
        payload["taskType"] = GEMINI_TASK_QUERY if for_query else GEMINI_TASK_DOCUMENT

    try:
        response = httpx.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json", "x-goog-api-key": GEMINI_API_KEY},
            timeout=120.0,
        )
        response.raise_for_status()
        values = _parse_gemini_embedding_payload(response.json())
        if values is None:
            logger.error("Unexpected Gemini embedContent response shape")
            return None
        return values
    except httpx.HTTPStatusError as e:
        logger.error(
            "Gemini embedContent HTTP error: %s — %s",
            e.response.status_code,
            e.response.text[:500] if e.response.text else "",
        )
        return None
    except httpx.RequestError as e:
        logger.error("Gemini embedContent request error: %s", e)
        return None


def _embedding_ollama_http(text: str):
    try:
        response = httpx.post(
            f"{OLLAMA_ENDPOINT}/api/embed",
            json={"model": OLLAMA_EMBEDDING_MODEL, "input": text},
            headers={"Content-Type": "application/json"},
            timeout=6000.0,
        )
        response.raise_for_status()
        data = response.json()
        embeddings = data.get("embeddings") if isinstance(data, dict) else None
        if not embeddings or not isinstance(embeddings[0], list):
            logger.error("Unexpected Ollama /api/embed response shape")
            return None
        return embeddings[0]
    except httpx.HTTPStatusError as e:
        logger.error(
            "Ollama embed HTTP error: %s — %s",
            e.response.status_code,
            e.response.text[:500] if e.response.text else "",
        )
        return None
    except httpx.RequestError as e:
        logger.error("Ollama embed request error: %s", e)
        return None


try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
except redis.exceptions.ConnectionError as e:
    logger.error(f"Could not connect to Redis: {e}")
    redis_client = None


async def get_embedding(text: str, *, for_query: bool = False):
    cache_key = _cache_key(text, for_query)

    if redis_client:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

    if EMBEDDING_ENGINE == "gemini":
        embedding_result = await asyncio.to_thread(_embedding_gemini_http, text, for_query)
    elif EMBEDDING_ENGINE == "ollama":
        await wait_for_embedding_service()
        embedding_result = await asyncio.to_thread(_embedding_ollama_http, text)
    else:
        logger.error("Unsupported EMBEDDING_ENGINE: %s", EMBEDDING_ENGINE)
        return None

    if isinstance(embedding_result, list) and redis_client and embedding_result:
        redis_client.setex(cache_key, CACHE_EXPIRATION_SECONDS, json.dumps(embedding_result))

    return embedding_result


if __name__ == "__main__":
    async def main():
        test_text = "這是一個測試句子，用於獲取其嵌入向量。"
        embedding_result = await get_embedding(test_text)
        if embedding_result:
            logger.info("Embedding 成功取得！")
            logger.info(f"Embedding 向量長度: {len(embedding_result)}")
            logger.info(f"前5個向量值: {embedding_result[:5]}")
        else:
            logger.error("Embedding 取得失敗。")

    asyncio.run(main())
