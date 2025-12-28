#!/bin/bash

# 偵測看看現在這個目錄底下的docker有沒有啟動。沒有的話，啟動它

cd $(dirname $0)

docker exec -it docker-external-knowledge-base-api-1 bash