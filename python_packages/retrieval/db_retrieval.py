import asyncio
import json
from ..ingest.ingest import ingest_data
from flask import Flask
from ..weaviate.weaviate_query import weaviate_query
from ..embedding.get_embedding import get_embedding
from ..knowledge_base_config.get_section_name import get_section_name
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config

app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

async def get_db_results(knowledge_id: str, section_name: str, query: str, top_k: int, score_threshold: float = None):
    """
    Retrieves results from the actual database based on the query, knowledge_id, top_k, and score_threshold.
    (Placeholder for actual database retrieval logic)
    """

    # ==============================
    asyncio.create_task(ingest_data(knowledge_id, section_name))

    # ==============================

    if section_name is None:
        section_name = get_section_name(knowledge_id)
    
    item_id = f"{knowledge_id}_{section_name}"
    config = get_knowledge_base_config(knowledge_id)
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

    return results

    # app.logger.info(f"Results from Weaviate query: {json.dumps(results, indent=2)}")

    # ==============================


    # In a real scenario, this would interact with a database
    # and return relevant results.
    # app.logger.debug(f"Performing database retrieval for knowledge_id: {knowledge_id}, query: {query}, top_k: {top_k}, score_threshold: {score_threshold}")
    
    # mock_db_results = [
    #     {
    #         "score": 0.80,
    #         "title": f"DB_knowledge_{knowledge_id}.txt",
    #         "content": f"DB 回覆：你查詢的是 {query}",
    #         "metadata": {
    #             "id": "db-001",
    #             "source": "real-db",
    #             "info": "這是真實資料庫結果"
    #         }
    #     },
    #     {
    #         "score": 0.60,
    #         "title": f"DB_another_knowledge_{knowledge_id}.txt",
    #         "content": f"DB 回覆：這是另一個關於 {query} 的結果",
    #         "metadata": {
    #             "id": "db-002",
    #             "source": "real-db",
    #             "info": "這是真實資料庫結果"
    #         }
    #     },
    #     {
    #         "score": 0.30,
    #         "title": f"DB_low_score_knowledge_{knowledge_id}.txt",
    #         "content": f"DB 回覆：這個結果分數較低，關於 {query}",
    #         "metadata": {
    #             "id": "db-003",
    #             "source": "real-db",
    #             "info": "這是真實資料庫結果"
    #         }
    #     }
    # ]

    # filtered_results = []
    # for result in mock_db_results:
    #     if score_threshold is None or result["score"] >= score_threshold:
    #         filtered_results.append(result)

    # return filtered_results[:top_k]
