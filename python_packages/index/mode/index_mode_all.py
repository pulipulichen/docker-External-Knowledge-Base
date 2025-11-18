import logging
from ...embedding.get_embedding import get_embedding
from ...weaviate.weaviate_add import weaviate_add
from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

logger = logging.getLogger(__name__)

BATCH = 100

async def index_mode_all(knowledge_id, section_name, chunks):
    
    config = get_knowledge_base_config(knowledge_id)
    if config.get('section'):
        item_id = f"{knowledge_id}"
    else:
        item_id = f"{knowledge_id}_{section_name}"

    # logger.info(f"Total number of chunks: {len(chunks)}")
    # if chunks:
    #     logger.info(f"Content of the last chunk: {chunks[-1]}")
    # else:
    #     logger.info("No chunks to process.")

    # logger.info(f"Adding chunks to Weaviate for item_id: {item_id}")

    # 把chunks依照BATCH數量分成多個batch_chunks
    for i in range(0, len(chunks), BATCH):
        batch_chunks = chunks[i:i + BATCH]

        # 首先，先把chunks裡面，沒有vector的，加上vector。
        for chunk in batch_chunks:
            if "vector" not in chunk:
                chunk["vector"] = await get_embedding(chunk["document"])
        
        logger.info(f"Adding batch {i // BATCH + 1} with {len(batch_chunks)} chunks.")
        weaviate_add(knowledge_id=item_id, data_rows=batch_chunks)
