from ..ingest.ingest import ingest_data
from flask import Flask

app = Flask(__name__) # Keep a dummy app for local testing if __name__ == '__main__'

def get_db_results(knowledge_id: str, section_name: str, query: str, top_k: int, score_threshold: float = None):
    """
    Retrieves results from the actual database based on the query, knowledge_id, top_k, and score_threshold.
    (Placeholder for actual database retrieval logic)
    """

    # ==============================
    ingest_data(knowledge_id, query, top_k, score_threshold)

    # In a real scenario, this would interact with a database
    # and return relevant results.
    # app.logger.debug(f"Performing database retrieval for knowledge_id: {knowledge_id}, query: {query}, top_k: {top_k}, score_threshold: {score_threshold}")
    
    mock_db_results = [
        {
            "score": 0.80,
            "title": f"DB_knowledge_{knowledge_id}.txt",
            "content": f"DB 回覆：你查詢的是 {query}",
            "metadata": {
                "id": "db-001",
                "source": "real-db",
                "info": "這是真實資料庫結果"
            }
        },
        {
            "score": 0.60,
            "title": f"DB_another_knowledge_{knowledge_id}.txt",
            "content": f"DB 回覆：這是另一個關於 {query} 的結果",
            "metadata": {
                "id": "db-002",
                "source": "real-db",
                "info": "這是真實資料庫結果"
            }
        },
        {
            "score": 0.30,
            "title": f"DB_low_score_knowledge_{knowledge_id}.txt",
            "content": f"DB 回覆：這個結果分數較低，關於 {query}",
            "metadata": {
                "id": "db-003",
                "source": "real-db",
                "info": "這是真實資料庫結果"
            }
        }
    ]

    filtered_results = []
    for result in mock_db_results:
        if score_threshold is None or result["score"] >= score_threshold:
            filtered_results.append(result)

    return filtered_results[:top_k]
