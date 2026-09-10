#!/bin/bash

cd $(dirname $0)

# 幫我做資料庫重置的功能
# 1. 停掉所有的docker容器
docker compose down
# 2. 刪除所有的docker容器
docker compose rm
# 3. 刪除所有的docker卷
docker compose down -v
# 4. 刪除所有的docker網路
docker compose down -v
# 5. 重新啟動所有的docker容器
docker compose up -d