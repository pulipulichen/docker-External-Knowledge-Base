#!/bin/bash

# Restart the project and print SUCCESSFUL only after every startup step
# has completed successfully.

set -Eeuo pipefail

cd "$(dirname "$0")"

fail() {
  local exit_code=$?
  echo
  echo "==========="
  echo "FAILED"
  echo "==========="
  exit "$exit_code"
}

trap fail ERR

sudo docker compose down

git pull

sudo docker compose down

sleep 2

# Do not background Compose: wait for build and service creation to complete.
# Default: build all services as before. On space-constrained deployments,
# STARTUP_BUILD_SERVICES="weaviate" builds only the named services, then
# reuses existing images for everything else.
if [[ -n "${STARTUP_BUILD_SERVICES:-}" ]]; then
  read -r -a build_services <<< "$STARTUP_BUILD_SERVICES"
  sudo docker compose build "${build_services[@]}"
  sudo docker compose up --no-build -d
else
  sudo docker compose up --build -d
fi

sleep 5

# Print a bounded log snapshot; logs.sh follows forever and would block SUCCESSFUL.
sudo docker compose logs --tail=40 --no-color

echo
echo "==========="
echo "SUCCESSFUL"
echo "==========="
