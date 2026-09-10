#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

git pull

docker-compose rm -sf nginx

docker-compose up -d --no-deps nginx