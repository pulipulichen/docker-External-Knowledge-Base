#!/bin/bash

rm -rf /tmp/convert_file_path_to_markdown_content.lock

exec gunicorn --chdir /app/markdown_converter --bind 0.0.0.0:80 --reload markdown_converter:app --workers 4 --threads 4 --timeout 120
