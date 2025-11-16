import httpx
import os
import logging
import asyncio

# Configure logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TEI_ENDPOINT = os.getenv("TEI_ENDPOINT", "http://tei_bge_m3:80")
SERVICE_CHECK_INTERVAL = int(os.getenv("SERVICE_CHECK_INTERVAL", 5)) # seconds

# *** 建議 1: 增加 Timeout ***
# 1 秒太短了，對於服務啟動來說可能不夠
SERVICE_CHECK_TIMEOUT = int(os.getenv("SERVICE_CHECK_TIMEOUT", 5)) # seconds

IS_SERVICE_ALIVE = False

async def wait_for_embedding_service():
    """
    Waits until the embedding service (TEI_ENDPOINT) is available.
    """
    if IS_SERVICE_ALIVE is True:
        return True

    logger.info(f"Waiting for embedding service at {TEI_ENDPOINT}...")
    logger.info(f"Check Timeout: {SERVICE_CHECK_TIMEOUT}s, Retry Interval: {SERVICE_CHECK_INTERVAL}s")

    while True:
        try:
            resp = httpx.get(TEI_ENDPOINT, timeout=SERVICE_CHECK_TIMEOUT)
            if resp.status_code == 200:
                logger.info("Embedding service is available!")
                break
        except httpx.HTTPStatusError as e:
            # 服務有回應，但是是 4xx 或 5xx 錯誤
            logger.warning(f"Service responded with error: {e.response.status_code}. Retrying in {SERVICE_CHECK_INTERVAL}s...")
        except httpx.RequestError as e:
            # *** 建議 2: 印出具體的錯誤類型 ***
            # 這是最關鍵的日誌，例如 ConnectError, ReadTimeout, ConnectTimeout
            logger.warning(f"Embedding service not yet available ({type(e).__name__}: {e}). Retrying in {SERVICE_CHECK_INTERVAL}s...")
        except Exception as e:
            # 捕捉其他非 httpx 的意外錯誤
            logger.error(f"An unexpected error occurred: {type(e).__name__}: {e}", exc_info=True)
            logger.error(f"Retrying in {SERVICE_CHECK_INTERVAL}s...")

        await asyncio.sleep(SERVICE_CHECK_INTERVAL)

    # logger.info("Check finished.")
    IS_SERVICE_ALIVE = True
    return True

if __name__ == "__main__":
    async def main():
        await wait_for_embedding_service()
        logger.info("Service check completed.")

    asyncio.run(main())
