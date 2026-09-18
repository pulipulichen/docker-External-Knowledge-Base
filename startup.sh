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

# Do not background this command: wait until compose has finished creating
# and starting all services before continuing.
sudo docker compose up --build -d

sleep 5

./logs.sh

echo
echo "==========="
echo "SUCCESSFUL"
echo "==========="
