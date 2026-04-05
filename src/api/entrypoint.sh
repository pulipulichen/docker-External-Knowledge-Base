#!/bin/bash

rm -rf /tmp/docker-External-Knowledge-Base-lock/*

gunicorn --bind 0.0.0.0:80 --reload api.api:app --workers 4 --threads 4 --timeout 120
