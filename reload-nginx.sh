#!/bin/bash

cd $(dirname $0)

git pull

docker-compose exec nginx nginx -t &&
docker-compose exec nginx nginx -s reload