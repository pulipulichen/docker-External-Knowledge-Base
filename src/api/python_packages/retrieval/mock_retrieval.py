def get_mock_results(knowledge_id: str, section_name: str, query: str, top_k: int, score_threshold: float = None):
    """
    Generates mock retrieval results based on the query, knowledge_id, top_k, and score_threshold.
    """
    mock_results = [
        {
            "score": 0.98,
            "title": f"knowledge_{knowledge_id}.txt",
            "content": f"This is the document for external knowledge related to {query}.",
            "metadata": {
                "path": f"s3://dify/knowledge_{knowledge_id}.txt",
                "description": f"dify knowledge document for {knowledge_id}"
            }
        },
        {
            "score": 0.75,
            "title": f"another_knowledge_{knowledge_id}.txt",
            "content": f"This is another document for external knowledge related to {query}.",
            "metadata": {
                "path": f"s3://dify/another_knowledge_{knowledge_id}.txt",
                "description": f"another dify knowledge document for {knowledge_id}"
            }
        },
        {
            "score": 0.40,
            "title": f"low_score_knowledge_{knowledge_id}.txt",
            "content": f"This document has a low score for {query}.",
            "metadata": {
                "path": f"s3://dify/low_score_knowledge_{knowledge_id}.txt",
                "description": f"low score dify knowledge document for {knowledge_id}"
            }
        }
    ]

    filtered_results = []
    for result in mock_results:
        if score_threshold is None or result["score"] >= score_threshold:
            filtered_results.append(result)

    return {
        "records": filtered_results[:top_k]
    }
