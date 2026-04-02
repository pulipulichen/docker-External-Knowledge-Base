#!/usr/bin/env bash

cd $(dirname $0)

source ../.env

# ===================

# 如果沒有啟動docker，那就啟動它
if ! sudo docker compose ps | grep -q "Up"; then
  echo "Docker services are not running. Starting them now..."
  sudo docker compose up -d
  echo "Docker services started."
else
  echo "Docker services are already running."
fi

# ===================

# 重複查詢兩次，中間間隔 10 秒 
for i in {1..2}; do
    curl -X POST http://localhost:8080/retrieval \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "knowledge_id": "example",
            "query": "webcam",
            "retrieval_setting": {
                "top_k": 5,
                "score_threshold": 0.1
            }
        }'

    sleep 10
done

# ===================
