import asyncio
import json
from flask import Flask
from ..weaviate.weaviate_query import weaviate_query
from ..embedding.get_embedding import get_embedding
from ..knowledge_base_config.get_section_name import get_section_name
from ..knowledge_base_config.get_knowledge_base_config import get_knowledge_base_config
from ..ingest.fire_and_forget_ingest import fire_and_forget_ingest
from ..ingest.ingest import ingest_data

import logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

# DEBUG = True
DEBUG = False

async def get_db_file_results(knowledge_id: str, section_name: str, query: str, top_k: int, score_threshold: float = None):
    """
    Retrieves results from the actual database based on the query, knowledge_id, top_k, and score_threshold.
    (Placeholder for actual database retrieval logic)
    """

    # force_update = False
    # force_update = True
    # ==============================
    # ✅ 丟到背景 thread，完全不等
    if DEBUG is False:
        force_update = False
        fire_and_forget_ingest(knowledge_id, section_name, force_update)
    else:
        force_update = True
        await ingest_data(knowledge_id, section_name, force_update)

    top_k_extend_range = 3

    # ==============================

    if section_name is None:
        section_name = get_section_name(knowledge_id)
    
    config = get_knowledge_base_config(knowledge_id)

    if config.get('section') or config.get('is_file') is False:
        item_id = f"{knowledge_id}"
    else:
        item_id = f"{knowledge_id}_{section_name}"
    # app.logger.info(f"Results from Weaviate query: {item_id}")

    results = weaviate_query(
        knowledge_id=item_id, 
        query=query,
        vector=await get_embedding(query),
        query_config={
            "max_results": top_k * top_k_extend_range,
            "score_threshold": score_threshold
        },
        path=config.get("path", None)
    )

    # 2. 根據 path 去重，並保留 score 最高的結果
    unique_results_map = {}

    # app.logger.info("results:" + json.dumps(results, ensure_ascii = False))
    
    for doc in results.get("records"):
        app.logger.info(json.dumps(doc, ensure_ascii = False))
        
        path = doc.get("metadata", {}).get("path")
        score = doc.get("score", 0) # 假設結果中有 score 欄位
        
        # 如果 path 還沒出現過，或者當前這筆 score 比存起來的更高
        if path not in unique_results_map or score > unique_results_map[path].get("score", 0):
            unique_results_map[path] = doc

    # 3. 按 score 排序並取前 top_k 個路徑
    top_paths_docs = sorted(
        unique_results_map.values(), 
        key=lambda x: x.get("score", 0), 
        reverse=True
    )[:top_k]

    # --- 💡 新增步驟：根據 path 重組完整文件 ---
    final_markdown_documents = []

    for seed_doc in top_paths_docs:
        target_path = seed_doc.get("metadata", {}).get("path")
        
        # 4. 再次檢索：撈出該 path 底下的「所有」chunks
        # 注意：這裡的 max_results 必須設得夠大，確保能涵蓋整份文件
        all_chunks_for_path = weaviate_query(
            knowledge_id=item_id,
            query=None,  # 這裡不需要語義搜尋，我們是要按屬性篩選
            query_config={
                "max_results": 1000, # 假設單一檔案不會超過 1000 個 chunk
                "filters": {         # 確保你的 weaviate_query 支援 filter path
                    "path": target_path 
                }
            }
        )

        # 5. 依照 _chunk_id 進行升序排序 (由小到大)
        sorted_chunks = sorted(
            all_chunks_for_path,
            key=lambda x: x.get("metadata", {}).get("_chunk_id", 0)
        )

        # 6. 合併內容轉為 Markdown 格式
        full_content = "\n\n".join([c.get("content", "") for c in sorted_chunks])
        
        # 將結果包裝成物件回傳
        final_markdown_documents.append({
            "path": target_path,
            "score": seed_doc.get("score"),
            "content": full_content
        })

    return final_markdown_documents