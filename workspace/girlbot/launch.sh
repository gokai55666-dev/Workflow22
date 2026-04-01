#!/bin/bash
# launch.sh - Girlbot Master Launcher for RunPod
# Integrates testv1 + queue API

set -e

WORKSPACE="/workspace"
GIRLBOT="${WORKSPACE}/girlbot"
LOG_DIR="${WORKSPACE}/logs"
mkdir -p ${LOG_DIR}

echo "🚀 Girlbot AI Studio - RunPod Edition"
echo "======================================"
echo "$(date)"
echo ""

# Helper functions
log() { echo "[$(date +%H:%M:%S)] $1"; }
check_port() { lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; }

# Check GPU
log "🔍 Checking GPU..."
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader | head -1 || log "⚠️ GPU check failed"

# 1. Ollama
if ! check_port 11434; then
    log "📦 Starting Ollama..."
    ollama serve > ${LOG_DIR}/ollama.log 2>&1 &
    sleep 5
    log "   Ollama started (PID: $!)"
else
    log "📦 Ollama already running"
fi

# 2. ComfyUI
if ! check_port 8188; then
    log "🎨 Starting ComfyUI..."
    cd ${WORKSPACE}/ComfyUI
    python3 main.py --listen 0.0.0.0 --port 8188 --highvram > ${LOG_DIR}/comfyui.log 2>&1 &
    sleep 10
    log "   ComfyUI started (PID: $!)"
else
    log "🎨 ComfyUI already running"
fi

# 3. Queue API
if ! check_port 8000; then
    log "⚡ Starting Queue API..."
    cd ${GIRLBOT}
    # Ensure dependencies
    pip install fastapi uvicorn aiohttp requests -q 2>/dev/null || true

    python3 queue_api.py > ${LOG_DIR}/api.log 2>&1 &
    sleep 3
    log "   API started on port 8000 (PID: $!)"
else
    log "⚡ Queue API already running"
fi

# 4. Streamlit Frontend
if ! check_port 8501; then
    log "🖥️  Starting Frontend..."
    cd ${GIRLBOT}
    streamlit run app_queue.py --server.port 8501 --server.address 0.0.0.0 > ${LOG_DIR}/streamlit.log 2>&1 &
    log "   Frontend started on port 8501 (PID: $!)"
else
    log "🖥️  Frontend already running"
fi

# Summary
echo ""
echo "======================================"
echo "✅ All services started!"
echo "======================================"
echo ""
echo "📍 Access Points:"
echo "   🎨 ComfyUI:  http://$(hostname -I | awk '{print $1}'):8188"
echo "   ⚡ API:      http://$(hostname -I | awk '{print $1}'):8000/docs"
echo "   🖥️  Frontend: http://$(hostname -I | awk '{print $1}'):8501"
echo "   🤖 Ollama:   http://$(hostname -I | awk '{print $1}'):11434"
echo ""
echo "📁 Logs: ${LOG_DIR}/"
echo "🔧 Management:"
echo "   Stop:  pkill -f 'ollama|comfyui|queue_api|streamlit'"
echo "   Logs:  tail -f ${LOG_DIR}/*.log"
echo ""
echo "💡 Usage:"
echo "   - Type 'draw: a sunset' to generate images"
echo "   - Toggle 'Use Queue' in sidebar for async mode"
echo ""

# Keep alive
if [ -t 0 ]; then
    log "Press Ctrl+C to stop..."
    wait
fi
