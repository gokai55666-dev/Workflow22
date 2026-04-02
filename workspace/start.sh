#!/bin/bash
# Create log dir
mkdir -p /workspace/logs

# Kill existing
pkill -f "python3 main.py" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "streamlit" 2>/dev/null || true
sleep 2

# Start ComfyUI
echo "Starting ComfyUI..."
cd /workspace/ComfyUI
nohup python3 main.py --listen 0.0.0.0 --port 8188 --highvram > /workspace/logs/comfyui.log 2>&1 &
echo "PID: $!"

# Wait
until curl -s http://localhost:8188/system_stats > /dev/null 2>&1; do sleep 2; done
echo "ComfyUI ready!"

# Start API
echo "Starting API..."
cd /workspace/Workflow22/workspace/girlbot
nohup uvicorn orchestrator:app --host 0.0.0.0 --port 8000 > /workspace/logs/api.log 2>&1 &
echo "PID: $!"

# Start UI
echo "Starting UI..."
nohup streamlit run app.py --server.port 8501 --server.address 0.0.0.0 > /workspace/logs/ui.log 2>&1 &
echo "PID: $!"

echo "All services started!"
