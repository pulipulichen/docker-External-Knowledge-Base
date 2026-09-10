#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

git pull

docker compose up -d \
  --force-recreate \
  --no-deps \
  nginx