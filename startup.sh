#!/bin/bash

# 偵測看看現在這個目錄底下的docker有沒有啟動。沒有的話，啟動它

docker compose down
docker compose up --build
