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


def _model_id_for_generate_content(model: str) -> str:
    m = model.strip()
    if m.startswith("models/"):
        return m[len("models/"):]
    return m


def _guess_image_mime_type(image_base64: str) -> str:
    """Infer MIME type from base64-decoded image magic bytes (default image/jpeg)."""
    raw = image_base64.strip()
    try:
        pad = len(raw) % 4
        if pad:
            raw += "=" * (4 - pad)
        head = base64.b64decode(raw[:128], validate=False)[:16]
    except Exception:
        return "image/jpeg"
    if head.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if head.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if head.startswith(b"GIF87a") or head.startswith(b"GIF89a"):
        return "image/gif"
    if len(head) >= 12 and head.startswith(b"RIFF") and head[8:12] == b"WEBP":
        return "image/webp"
    return "image/jpeg"


def _text_from_generate_content_response(body: dict) -> str:
    candidates = body.get("candidates") or []
    if not candidates:
        feedback = body.get("promptFeedback") or {}
        block = feedback.get("blockReason")
        if block:
            raise ValueError(f"Gemini blocked the request: {block}")
        raise ValueError("Gemini returned no candidates")
    parts = (candidates[0].get("content") or {}).get("parts") or []
    texts = [p.get("text", "") for p in parts if isinstance(p, dict) and "text" in p]
    out = "".join(texts).strip()
    if not out:
        raise ValueError("Gemini returned empty text")
    return out


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

    # If not in cache, call Gemini API (REST generateContent)
    prompt = get_prompt()
    model_id = _model_id_for_generate_content(GEMINI_MODEL)
    api_url = (
        f"{GEMINI_BASE_URL.rstrip('/')}/v1beta/models/{model_id}:generateContent"
    )
    mime_type = _guess_image_mime_type(image_base64)

    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_base64,
                        }
                    },
                    {"text": prompt},
                ],
            }
        ]
    }

    try:
        response = requests.post(api_url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        description = _text_from_generate_content_response(result)
        
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
