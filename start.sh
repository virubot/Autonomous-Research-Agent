#!/bin/bash
set -e

PORT=${PORT:-8080}

echo "Starting FastAPI on port $PORT"

exec uvicorn backend.main:app --host 0.0.0.0 --port $PORT