from ...embedding.get_embedding import get_embedding
from ...weaviate.weaviate_add import weaviate_add
import logging

from ...weaviate.weaviate_ready import weaviate_ready

from ...knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

from .index_mode_all import index_mode_all

def index_mode_last(knowledge_id, section_name, chunks):

    config = get_knowledge_base_config(knowledge_id)
    length = config.get("index", {}).get("length", 100)
    
    item_id = f"{knowledge_id}_{section_name}"

    is_ready = weaviate_ready(knowledge_id=item_id)

    if is_ready is True:

        last_chunks = chunks[:length]

        logging.info(f"Number of last_chunks: {len(last_chunks)}")
        if last_chunks:
            logging.info(f"Content of the last chunk: {last_chunks[-1]}")

        for chunk in last_chunks:
            if "vector" not in chunk:
                chunk["vector"] = get_embedding(chunk["document"])

        # return weaviate_add(knowledge_id=item_id, data_rows=last_chunks)
    else:
        return index_mode_all(knowledge_id, section_name, chunks)
