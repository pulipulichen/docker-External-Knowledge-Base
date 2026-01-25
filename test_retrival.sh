#!/bin/bash

cd $(dirname $0)

source .env

curl -X POST http://localhost:8080/retrieval \
    -H "Authorization: Bearer $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{
        "knowledge_id": "prefer_terms",
        "query": "攝像頭",
        "retrieval_setting": {
            "top_k": 5,
            "score_threshold": 0.1
        }
    }'


# curl -X POST http://api/retrieval \
#     -H "Authorization: Bearer $API_KEY" \
#     -H "Content-Type: application/json" \
#     -d '{
#         "knowledge_id": "example",
#         "query": "擴銷",
#         "retrieval_setting": {
#             "top_k": 5,
#             "score_threshold": 0.7
#         }
#     }'