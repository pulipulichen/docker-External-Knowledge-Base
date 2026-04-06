import os
import base64
import hashlib
import redis
import requests
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
CACHE_EXPIRATION_SECONDS = int(os.getenv("CACHE_EXPIRATION_SECONDS", 2592000))

GEMINI_BASE_URL = os.getenv("GEMINI_BASE_URL", "https://generativelanguage.googleapis.com")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")

# Initialize Redis client
redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def get_prompt():
    prompt_path = Path(__file__).parent / "image_describe_prompt.txt"
    if prompt_path.exists():
        return prompt_path.read_text(encoding="utf-8").strip()
    return "Please describe this image."

def image_describe(image_base64: str) -> str:
    """
    Analyzes an image provided as base64 and returns a description.
    Uses Redis to cache results.
    """
    if not image_base64:
        return ""
    
    if GEMINI_API_KEY == "YOUR_GEMINI_API_KEY":
        raise ValueError("Please set GEMINI_API_KEY environment variable.")

    # Generate a unique key for caching based on image content (SHA256)
    image_hash = hashlib.sha256(image_base64.encode('utf-8')).hexdigest()
    cache_key = f"image_desc:{image_hash}"

    # Check cache
    cached_result = redis_client.get(cache_key)
    if cached_result:
        logger.info(f"Serving image description from cache for hash: {image_hash}")
        return cached_result

    # If not in cache, call Gemini API
    prompt = get_prompt()
    
    # API Endpoint (assuming OpenAI-compatible proxy)
    api_url = f"{GEMINI_BASE_URL.rstrip('/')}/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GEMINI_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": GEMINI_MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        description = result['choices'][0]['message']['content'].strip()
        
        # Cache the result
        redis_client.setex(cache_key, CACHE_EXPIRATION_SECONDS, description)
        logger.info(f"Cached image description for hash: {image_hash}")
        
        return description
        
    except Exception as e:
        logger.error(f"Error calling Gemini API: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    # Simple test if run directly
    # Note: requires a valid base64 image or this will fail
    pass
