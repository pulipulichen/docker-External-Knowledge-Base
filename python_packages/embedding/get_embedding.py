import requests
import os
import redis
import json

TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "http://tei_bge_m3:80")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", 3600)) # Cache for 1 hour

# Initialize Redis client
try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    redis_client.ping()
    print("Connected to Redis successfully!")
except redis.exceptions.ConnectionError as e:
    print(f"Could not connect to Redis: {e}")
    redis_client = None

def get_embedding(text: str):
    """
    取得輸入字串的 embedding 結果。
    """
    if redis_client:
        cache_key = f"embedding:{text}"
        cached_result = redis_client.get(cache_key)
        if cached_result:
            print(f"Cache hit for text: {text[:30]}...")
            return json.loads(cached_result)

    try:
        response = requests.post(
            f"{TEI_ENDPOINT}/embed",
            json={"inputs": text},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        response.raise_for_status()  # Raises HTTPError for bad responses (4xx or 5xx)
        embedding_result = response.json()

        if redis_client and embedding_result:
            redis_client.setex(cache_key, CACHE_EXPIRATION_SECONDS, json.dumps(embedding_result))
            print(f"Cached embedding for text: {text[:30]}...")
        
        return embedding_result
    except requests.exceptions.RequestException as e:
        print(f"Error getting embedding: {e}")
        return None

if __name__ == "__main__":
    test_text = "這是一個測試句子，用於獲取其嵌入向量。"
    embedding_result = get_embedding(test_text)

    if embedding_result:
        print("Embedding 成功取得！")
        print(f"Embedding 向量長度: {len(embedding_result[0])}")
        print(f"前5個向量值: {embedding_result[0][:5]}")
    else:
        print("Embedding 取得失敗。")

    test_text_2 = "第二個測試句子。"
    embedding_result_2 = get_embedding(test_text_2)

    if embedding_result_2:
        print("第二個 Embedding 成功取得！")
        print(f"Embedding 向量長度: {len(embedding_result_2[0])}")
    else:
        print("第二個 Embedding 取得失敗。")
