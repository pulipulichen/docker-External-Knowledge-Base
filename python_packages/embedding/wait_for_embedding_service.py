import asyncio
import httpx
import os
import logging

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "http://tei_bge_m3:80")
SERVICE_CHECK_INTERVAL = int(os.getenv("SERVICE_CHECK_INTERVAL", 5)) # seconds
SERVICE_CHECK_TIMEOUT = int(os.getenv("SERVICE_CHECK_TIMEOUT", 1)) # seconds

async def wait_for_embedding_service():
    """
    Waits until the embedding service (TEI_ENDPOINT) is available.
    """
    logger.info(f"Waiting for embedding service at {TEI_ENDPOINT}...")
    while True:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{TEI_ENDPOINT}/health", timeout=SERVICE_CHECK_TIMEOUT)
                response.raise_for_status()
            logger.info("Embedding service is available!")
            break
        except (httpx.RequestError, httpx.HTTPStatusError) as e:
            logger.warning(f"Embedding service not yet available: {e}. Retrying in {SERVICE_CHECK_INTERVAL} seconds...")
            await asyncio.sleep(SERVICE_CHECK_INTERVAL)

if __name__ == "__main__":
    async def main():
        await wait_for_embedding_service()
        logger.info("Service check completed.")

    asyncio.run(main())
