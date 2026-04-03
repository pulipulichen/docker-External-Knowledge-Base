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
curl -X POST http://localhost:8080/news \
        -H "Authorization: Bearer $API_KEY" \
        -H "Content-Type: application/json" \
        -d '{
            "query": "伊朗 戰爭 美國 結果",
        }'

# ===================
