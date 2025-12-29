import logging
from ...embedding.get_embedding import get_embedding
from ...weaviate.weaviate_add import weaviate_add
from ...weaviate.weaviate_close import weaviate_close
from ...weaviate.weaviate_clear_relative_path import weaviate_clear_relative_path
from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
import os
from ..chunk.get_chunks_from_markdown_file import get_chunks_from_markdown_file
from ..chunk.get_chunks_from_markdown_file import get_relative_path

logger = logging.getLogger(__name__)

BATCH = 100

async def index_mode_file(knowledge_id, markdown_file_path):
    
    # config = get_knowledge_base_config(knowledge_id)

    # weaviate_add(knowledge_id=knowledge_id, data_rows=batch_chunks)
    clear_db_file_path(knowledge_id, markdown_file_path)
    # return False

    chunks = get_chunks_from_markdown_file(knowledge_id, markdown_file_path)
    
    index_result = False

    if not isinstance(chunks, list):
        logger.error(f"chunks is not a list: {type(chunks)}")
        return index_result
    
    # logger.info(await get_embedding("測試"))
    logger.info(f"Length of chunks: {len(chunks)}")
    # logger.info(f"Content of the last chunk: {chunks[-1]}")

    # 把chunks依照BATCH數量分成多個batch_chunks
    for i in range(0, len(chunks), BATCH):
        batch_chunks = chunks[i:i + BATCH]

        # logger.info(f"Length of batch_chunks: {len(batch_chunks)}")
        # logger.info(f"Content of the last chunk: {batch_chunks[0]}")

        # 首先，先把chunks裡面，沒有vector的，加上vector。
        for chunk in batch_chunks:
            if "vector" not in chunk and "document" in chunk:
                chunk["vector"] = await get_embedding(chunk["document"])

            # document = chunk.get('document')
            # logger.info(f"document: {type(chunk)}")

            if "document" not in chunk:
                continue
        
        # logger.info(f"Adding batch {i // BATCH + 1} with {len(batch_chunks)} chunks.")
        
        if weaviate_add(knowledge_id=knowledge_id, data_rows=batch_chunks) is True:
            index_result = True

    # weaviate_close()
    return index_result

def clear_db_file_path(knowledge_id, markdown_file_path):
    relative_path = get_relative_path(markdown_file_path)

    weaviate_clear_relative_path(knowledge_id=knowledge_id, relative_path=relative_path)