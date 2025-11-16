def get_db_results(query: str, top_k: int):
    """
    Retrieves results from the actual database based on the query.
    (Placeholder for actual database retrieval logic)
    """
    # In a real scenario, this would interact with a database
    # and return relevant results.
    print(f"Performing database retrieval for query: {query}, top_k: {top_k}")
    return [
        {
            "score": 0.80,
            "text": f"DB 回覆：你查詢的是 {query}",
            "metadata": {
                "id": "db-001",
                "source": "real-db",
                "info": "這是真實資料庫結果"
            }
        }
    ]
