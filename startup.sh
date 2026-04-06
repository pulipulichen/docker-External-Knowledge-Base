#!/bin/bash

# 偵測看看現在這個目錄底下的docker有沒有啟動。沒有的話，啟動它

cd $(dirname $0)

sudo docker compose down

git pull

sudo docker compose down

sleep 2

sudo docker compose up --build -d &

sleep 5

./logs.sh
