#!/bin/bash

set -e

echo "Starting ParcelPilot FastAPI backend..."

uvicorn src.api:app \
    --host 127.0.0.1 \
    --port 8000 &

echo "Starting ParcelPilot Streamlit frontend..."

exec streamlit run streamlit_app.py \
    --server.address 0.0.0.0 \
    --server.port ${PORT:-7860} \
    --server.headless true