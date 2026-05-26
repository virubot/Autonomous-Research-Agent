#!/bin/bash
set -e

echo "Starting FastAPI on port ${PORT:-8080}"

uvicorn backend.main:app \
  --host 0.0.0.0 \
  --port ${PORT:-8080}