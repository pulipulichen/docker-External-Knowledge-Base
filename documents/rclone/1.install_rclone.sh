#!/bin/bash

if ! command -v rclone &> /dev/null
then
    echo "rclone could not be found, installing..."
    apt update
    apt install -y rclone
else
    echo "rclone is already installed."
fi
