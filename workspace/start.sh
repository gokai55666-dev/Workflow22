#!/bin/bash

echo "Starting ComfyUI..."
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188 --highvram &

# Wait for ComfyUI to be fully ready before starting API
echo "Waiting for ComfyUI to initialize..."
until curl -s http://localhost:8188/system_stats > /dev/null 2>&1; do
    sleep 2
done
echo "ComfyUI ready!"

echo "Starting API..."
cd /workspace/Workflow22/workspace/girlbot
uvicorn orchestrator:app --host 0.0.0.0 --port 8000 &

echo "Starting UI..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
