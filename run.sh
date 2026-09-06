#!/bin/sh
set -eu

cd backend
uv run fastapi dev
