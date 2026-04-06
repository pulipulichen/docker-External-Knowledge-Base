import asyncio
import httpx
import os
import redis
import json
import logging

from .wait_for_embedding_service import wait_for_embedding_service

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

EMBEDDING_ENGINE = os.getenv("EMBEDDING_ENGINE", "tei").strip().lower()
TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "http://tei:80")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", 3600))

# 與 [api] 的 GEMINI_BASE_URL（聊天／代理）分開，避免誤打到非 embed 端點
GEMINI_EMBEDDING_BASE_URL = os.getenv(
    "GEMINI_EMBEDDING_BASE_URL",
    "https://generativelanguage.googleapis.com",
).rstrip("/")
GEMINI_EMBEDDING_MODEL = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-2-preview")
GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
GEMINI_TASK_QUERY = os.getenv("GEMINI_EMBEDDING_TASK_TYPE_QUERY", "RETRIEVAL_QUERY").strip()
GEMINI_TASK_DOCUMENT = os.getenv("GEMINI_EMBEDDING_TASK_TYPE_DOCUMENT", "RETRIEVAL_DOCUMENT").strip()
_GEMINI_OUT_DIM_RAW = os.getenv("GEMINI_OUTPUT_DIMENSIONALITY", "").strip()


def _cache_key(text: str, for_query: bool) -> str:
    return f"embedding:{EMBEDDING_ENGINE}:q={int(for_query)}:{text}"


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
    payload = {
        "content": {"parts": [{"text": body_text}]},
    }
    if _GEMINI_OUT_DIM_RAW:
        payload["outputDimensionality"] = int(_GEMINI_OUT_DIM_RAW)

    if not _gemini_uses_prompt_task_prefix(model):
        payload["taskType"] = GEMINI_TASK_QUERY if for_query else GEMINI_TASK_DOCUMENT

    try:
        response = httpx.post(
            url,
            json=payload,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": GEMINI_API_KEY,
            },
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


try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
except redis.exceptions.ConnectionError as e:
    logger.error(f"Could not connect to Redis: {e}")
    redis_client = None


async def get_embedding(text: str, *, for_query: bool = False):
    """
    取得輸入字串的 embedding。
    for_query：使用 Gemini 時區分檢索查詢與文件片段（官方非對稱格式 / taskType）。
    TEI 路徑會忽略此旗標。
    """
    cache_key = _cache_key(text, for_query)

    if redis_client:
        cached_result = redis_client.get(cache_key)
        if cached_result:
            return json.loads(cached_result)

    try:
        if EMBEDDING_ENGINE == "gemini":
            embedding_result = await asyncio.to_thread(_embedding_gemini_http, text, for_query)
        else:
            await wait_for_embedding_service()
            response = httpx.post(
                f"{TEI_ENDPOINT}/embed",
                json={"inputs": text},
                headers={"Content-Type": "application/json"},
                timeout=6000,
            )
            response.raise_for_status()
            embedding_result = response.json()
            if isinstance(embedding_result[0], list):
                embedding_result = embedding_result[0]

        if isinstance(embedding_result, list) and redis_client and embedding_result:
            redis_client.setex(cache_key, CACHE_EXPIRATION_SECONDS, json.dumps(embedding_result))

        return embedding_result
    except httpx.RequestError as e:
        logger.error(f"Error getting embedding: {e}")
        return None


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

        test_text_2 = "第二個測試句子。"
        embedding_result_2 = await get_embedding(test_text_2)

        if embedding_result_2:
            logger.info("第二個 Embedding 成功取得！")
            logger.info(f"Embedding 向量長度: {len(embedding_result_2)}")
        else:
            logger.error("第二個 Embedding 取得失敗。")

    asyncio.run(main())
