def get_mock_results(query: str, top_k: int):
    """
    Generates mock retrieval results based on the query.
    """
    mock_results = [
        {
            "score": 0.95,
            "text": f"Mock 回覆：你查詢的是 {query}",
            "metadata": {
                "id": "mock-001",
                "source": "mock-db",
                "info": "這是範例結果"
            }
        }
    ]
    return mock_results[:top_k]
