#!/bin/bash

exec gunicorn --chdir /app/markdown_converter --bind 0.0.0.0:80 --reload markdown_converter:app --workers 4 --threads 4 --timeout 120
