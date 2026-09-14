import httpx
import os
import logging
import asyncio

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

OLLAMA_ENDPOINT = os.getenv("OLLAMA_ENDPOINT", "http://ollama:11434").rstrip("/")
EMBEDDING_ENGINE = os.getenv("EMBEDDING_ENGINE", "ollama").strip().lower()
EMBEDDING_ENGINE = "ollama" if EMBEDDING_ENGINE == "tei" else EMBEDDING_ENGINE
SERVICE_CHECK_INTERVAL = int(os.getenv("SERVICE_CHECK_INTERVAL", 5))
SERVICE_CHECK_TIMEOUT = int(os.getenv("SERVICE_CHECK_TIMEOUT", 60))

IS_SERVICE_ALIVE = False


async def wait_for_embedding_service():
    global IS_SERVICE_ALIVE

    if EMBEDDING_ENGINE == "gemini":
        IS_SERVICE_ALIVE = True
        return True

    if EMBEDDING_ENGINE != "ollama":
        raise RuntimeError(f"Unsupported EMBEDDING_ENGINE: {EMBEDDING_ENGINE}")

    if IS_SERVICE_ALIVE:
        return True

    while True:
        try:
            resp = httpx.get(OLLAMA_ENDPOINT, timeout=SERVICE_CHECK_TIMEOUT)
            if resp.status_code == 200:
                IS_SERVICE_ALIVE = True
                return True
            logger.warning("Ollama responded with HTTP %s. Retrying in %ss...", resp.status_code, SERVICE_CHECK_INTERVAL)
        except httpx.RequestError as e:
            logger.warning("Ollama not yet available (%s: %s). Retrying in %ss...", type(e).__name__, e, SERVICE_CHECK_INTERVAL)
        except Exception as e:
            logger.error("Unexpected embedding service check error: %s: %s", type(e).__name__, e, exc_info=True)

        await asyncio.sleep(SERVICE_CHECK_INTERVAL)


if __name__ == "__main__":
    async def main():
        await wait_for_embedding_service()
        logger.info("Embedding service check completed.")

    asyncio.run(main())
