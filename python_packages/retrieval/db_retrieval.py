import asyncio
import json
from ..ingest.ingest import ingest_data
from flask import Flask
from ..weaviate.weaviate_query import weaviate_query
from ..embedding.get_embedding import get_embedding
from ..knowledge_base_config.get_section_name import get_section_name
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

import threading
import asyncio

def fire_and_forget_ingest(knowledge_id: str, section_name: str):
    def runner():
        # 每個 thread 自己開一個 event loop
        asyncio.run(ingest_data(knowledge_id, section_name))

    t = threading.Thread(target=runner, daemon=True)
    t.start()

async def get_db_results(knowledge_id: str, section_name: str, query: str, top_k: int, score_threshold: float = None):
    """
    Retrieves results from the actual database based on the query, knowledge_id, top_k, and score_threshold.
    (Placeholder for actual database retrieval logic)
    """

    # ==============================
    # ✅ 丟到背景 thread，完全不等
    fire_and_forget_ingest(knowledge_id, section_name)

    # ==============================

    if section_name is None:
        section_name = get_section_name(knowledge_id)
    
    config = get_knowledge_base_config(knowledge_id)

    if config.get('section'):
        item_id = f"{knowledge_id}"
    else:
        item_id = f"{knowledge_id}_{section_name}"
    # app.logger.info(f"Results from Weaviate query: {item_id}")

    results = weaviate_query(
        knowledge_id=item_id, 
        query=query,
        vector=await get_embedding(query),
        query_config={
            "max_results": top_k,
            "score_threshold": score_threshold
        },
        path=config.get("path", None)
    )

    # app.logger.info(f"Results from Weaviate query: {json.dumps(results, indent=2)}")

    return results
