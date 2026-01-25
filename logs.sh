#!/bin/bash

# 偵測看看現在這個目錄底下的docker有沒有啟動。沒有的話，啟動它

if ! sudo docker compose ps | grep -q "Up"; then
  echo "Docker services are not running. Starting them now..."
  sudo docker compose up -d
  echo "Docker services started."
else
  echo "Docker services are already running."
fi

sudo docker compose logs -f
