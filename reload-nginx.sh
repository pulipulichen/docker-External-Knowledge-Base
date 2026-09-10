#!/bin/bash

cd $(dirname $0)

git pull

docker-compose up -d \
  --force-recreate \
  --no-deps \
  nginx