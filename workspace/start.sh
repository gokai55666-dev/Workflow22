#!/bin/bash

echo "Starting ComfyUI..."
cd /workspace/ComfyUI
python3 main.py --listen 0.0.0.0 --port 8188 --highvram &

echo "Starting API..."
cd /workspace/Workflow22/workspace/girlbot
uvicorn orchestrator:app --host 0.0.0.0 --port 8000 &

echo "Starting UI..."
streamlit run app.py --server.port 8501 --server.address 0.0.0.0