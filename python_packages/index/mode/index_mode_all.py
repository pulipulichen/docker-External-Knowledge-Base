import logging
from ...embedding.get_embedding import get_embedding
from ...weaviate.weaviate_add import weaviate_add

logger = logging.getLogger(__name__)

async def index_mode_all(knowledge_id, section_name, chunks):
    
    item_id = f"{knowledge_id}_{section_name}"

    # logger.info(await get_embedding('測試'))

    # 首先，先把chunks裡面，沒有vector的，加上vector。
    for chunk in chunks:
        if "vector" not in chunk:
            chunk["vector"] = await get_embedding(chunk["document"])


    # 用logger記錄，總共多少個chunks，然後最後一個chunk的內容
    # logger.info(f"Total number of chunks: {len(chunks)}")
    # if chunks:
    #     logger.info(f"Content of the last chunk: {chunks[-1]}")
    # else:
    #     logger.info("No chunks to process.")

    # logger.info(f"{item_id}")

    weaviate_add(knowledge_id=item_id, data_rows=chunks)
    # success = weaviate_add(knowledge_id=item_id, data_rows=chunks)
    # return success
