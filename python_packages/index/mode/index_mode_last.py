from ...embedding.get_embedding import get_embedding
from ...weaviate.weaviate_add import weaviate_add
import logging
logger = logging.getLogger(__name__)

from ...weaviate.weaviate_ready import weaviate_ready

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from .index_mode_all import index_mode_all

BATCH = 100

async def index_mode_last(knowledge_id, section_name, chunks):

    config = get_knowledge_base_config(knowledge_id)
    length = config.get("index", {}).get("length", 100)
    
    if config.get('section'):
        item_id = f"{knowledge_id}"
    else:
        item_id = f"{knowledge_id}_{section_name}"

    is_ready = weaviate_ready(knowledge_id=item_id)

    if is_ready is True:

        last_chunks = chunks[-length:]

        # logging.info(f"Number of last_chunks ({length}): {len(last_chunks)} - {len(chunks)}")
        # if last_chunks:
        #     logging.info(f"Content of the last chunk: {last_chunks[-1]}")

        for i in range(0, len(last_chunks), BATCH):
            batch_chunks = last_chunks[i:i + BATCH]

            # 首先，先把chunks裡面，沒有vector的，加上vector。
            for chunk in batch_chunks:
                if "vector" not in chunk:
                    chunk["vector"] = await get_embedding(chunk["document"])
            
            # logger.info(f"Adding batch {i // BATCH + 1} with {len(batch_chunks)} chunks.")
            weaviate_add(knowledge_id=item_id, data_rows=batch_chunks)
        
        return last_chunks
    else:
        return await index_mode_all(knowledge_id, section_name, chunks)
