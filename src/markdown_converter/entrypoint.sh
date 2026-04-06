#!/bin/bash

gunicorn --bind 0.0.0.0:80 --reload markdown_converter.markdown_converter:app --workers 4 --threads 4 --timeout 120
