#!/bin/sh
set -eu

cd /app
uv run fastapi run main.py --host 0.0.0.0 --port 8080
