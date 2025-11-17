import asyncio
import httpx
import os
import redis
import json
import logging

from .wait_for_embedding_service import wait_for_embedding_service

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "http://tei_bge_m3:80")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", 3600)) # Cache for 1 hour

# Initialize Redis client
try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
    # logger.info("Connected to Redis successfully!")
except redis.exceptions.ConnectionError as e:
    logger.error(f"Could not connect to Redis: {e}")
    redis_client = None

async def get_embedding(text: str):
    """
    取得輸入字串的 embedding 結果。
    """
    if redis_client:
        cache_key = f"embedding:{text}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            # logger.info(f"Cache hit for text: {text[:30]}...")
            return json.loads(cached_result)

    try:
        await wait_for_embedding_service()

        # async with httpx.AsyncClient() as client:
        #     response = await client.post(
        #         f"{TEI_ENDPOINT}/embed",
        #         json={"inputs": text},
        #         headers={"Content-Type": "application/json"},
        #         timeout=10
        #     )
        response = httpx.post(
                f"{TEI_ENDPOINT}/embed",
                json={"inputs": text},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        embedding_result = response.json()
        
        if isinstance(embedding_result[0], list):
            embedding_result = embedding_result[0]

        if isinstance(embedding_result, list) and redis_client and embedding_result:
            redis_client.setex(cache_key, CACHE_EXPIRATION_SECONDS, json.dumps(embedding_result))
            # logger.info(f"Cached embedding for text: {text[:30]}...")
        
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
            logger.info(f"Embedding 向量長度: {len(embedding_result[0])}")
            logger.info(f"前5個向量值: {embedding_result[0][:5]}")
        else:
            logger.error("Embedding 取得失敗。")

        test_text_2 = "第二個測試句子。"
        embedding_result_2 = await get_embedding(test_text_2)

        if embedding_result_2:
            logger.info("第二個 Embedding 成功取得！")
            logger.info(f"Embedding 向量長度: {len(embedding_result_2[0])}")
        else:
            logger.error("第二個 Embedding 取得失敗。")
    
    asyncio.run(main())
