from ...embedding.get_embedding import get_embedding
from ...weaviate.weaviate_add import weaviate_add

def index_mode_all(knowledge_id, section_name, chunks):
    
    item_id = f"{knowledge_id}_{section_name}"

    # 首先，先把chunks裡面，沒有vector的，加上vector。
    for chunk in chunks:
        if "vector" not in chunk:
            chunk["vector"] = get_embedding(chunk["document"])

    success = weaviate_add(knowledge_id=item_id, data_rows=chunks)
    return success