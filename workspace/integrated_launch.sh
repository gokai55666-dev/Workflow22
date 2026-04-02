#!/bin/bash
# ============================================================
# GIRL BOT AI - INTEGRATED LAUNCH (integrated_launch.sh)
# Launches Ollama, ComfyUI, Workflow22 Queue API, and Streamlit Frontend.
# Safe to re-run.
# ============================================================

set -e

WORKSPACE="/workspace"
GIRLBOT="${WORKSPACE}/girlbot"
LOG_DIR="${WORKSPACE}/logs"
mkdir -p ${LOG_DIR}

log() { echo "[$(date +%H:%M:%S)] $1"; }
check_port() { lsof -Pi :$1 -sTCP:LISTEN -t >/dev/null 2>&1; }

echo "🚀 Girlbot AI Studio - Integrated Launch"
echo "======================================"
echo "$(date)"
echo ""

# --- Kill any stale services ---
log "Cleaning up old processes..."
pkill -9 -f "ollama serve" 2>/dev/null || true
pkill -9 -f "streamlit" 2>/dev/null || true
pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "python.*main.py" 2>/dev/null || true # For ComfyUI
sleep 3

# ============================================================
# SERVICE 1: OLLAMA
# ============================================================
log "[1/4] Starting Ollama..."
if ! check_port 11434; then
    OLLAMA_MODELS=/workspace/ollama OLLAMA_HOST=0.0.0.0:11434 \
        nohup ollama serve > ${LOG_DIR}/ollama.log 2>&1 &
    # Health loop - wait up to 40s
    for i in $(seq 1 20); do
        if curl -s http://localhost:11434/api/tags >/dev/null 2>&1; then
            log "  ✅ Ollama ready (${i}x2s)"
            break
        fi
        sleep 2
        [ $i -eq 20 ] && { log "  ❌ Ollama failed to start! Check: tail -20 ${LOG_DIR}/ollama.log"; exit 1; }
    done
else
    log "  ✅ Ollama already running"
fi

# Pull model only if not already present
if ! OLLAMA_MODELS=/workspace/ollama ollama list 2>/dev/null | grep -q "dolphin-llama3"; then
    log "  Pulling dolphin-llama3:8b (first time, ~4GB)..."
    OLLAMA_MODELS=/workspace/ollama ollama pull dolphin-llama3:8b
    # Update config to mark model as pulled
    python3 -c "
import json
with open(\"${WORKSPACE}/system/config.json\", \"r\") as f: c = json.load(f)
c[\"model\"][\"pulled\"] = True
with open(\"${WORKSPACE}/system/config.json\", \"w\") as f: json.dump(c, f, indent=2)
" 2>/dev/null || true
else
    log "  ✅ Model already pulled, skipping download"
fi

# ============================================================
# SERVICE 2: COMFYUI
# ============================================================
log "[2/4] Starting ComfyUI..."
if ! check_port 8188; then
    if [ ! -f "${WORKSPACE}/ComfyUI/main.py" ]; then
        log "  ❌ ComfyUI not found! Run integrated_master_install.sh first."
        exit 1
    fi
    cd ${WORKSPACE}/ComfyUI
    nohup python3 main.py \
        --listen 0.0.0.0 \
        --port 8188 \
        --highvram \
        > ${LOG_DIR}/comfyui.log 2>&1 &
    cd ${WORKSPACE}
    # Health loop - ComfyUI takes longer on cold GPU, wait up to 90s
    for i in $(seq 1 45); do
        if curl -s http://localhost:8188/system_stats >/dev/null 2>&1; then
            log "  ✅ ComfyUI ready (${i}x2s)"
            break
        fi
        sleep 2
        [ $i -eq 45 ] && { log "  ❌ ComfyUI failed! Check: tail -30 ${LOG_DIR}/comfyui.log"; exit 1; }
    done
else
    log "  ✅ ComfyUI already running"
fi

# ============================================================
# SERVICE 3: WORKFLOW22 QUEUE API
# ============================================================
log "[3/4] Starting Workflow22 Queue API..."
if ! check_port 8000; then
    if [ ! -f "${GIRLBOT}/queue_api.py" ]; then
        log "  ❌ queue_api.py not found! Run integrated_master_install.sh first."
        exit 1
    fi
    cd ${GIRLBOT}
    nohup uvicorn queue_api:app --host 0.0.0.0 --port 8000 > ${LOG_DIR}/queue_api.log 2>&1 &
    cd ${WORKSPACE}
    # Health loop
    for i in $(seq 1 15); do
        if curl -s http://localhost:8000/health >/dev/null 2>&1; then
            log "  ✅ Queue API ready (${i}x2s)"
            break
        fi
        sleep 2
        [ $i -eq 15 ] && { log "  ❌ Queue API failed! Check: tail -20 ${LOG_DIR}/queue_api.log"; exit 1; }
    done
else
    log "  ✅ Queue API already running"
fi

# ============================================================
# SERVICE 4: STREAMLIT FRONTEND (Queue-aware)
# ============================================================
log "[4/4] Starting Streamlit Frontend..."
if ! check_port 8501; then
    if [ ! -f "${GIRLBOT}/app.py" ]; then
        log "  ❌ Streamlit app.py not found! Ensure it's copied to ${GIRLBOT}."
        exit 1
    fi
    cd ${GIRLBOT}
    nohup streamlit run app.py \
        --server.address 0.0.0.0 \
        --server.port 8501 \
        --server.headless true \
        > ${LOG_DIR}/streamlit.log 2>&1 &
    cd ${WORKSPACE}
    # Health loop
    for i in $(seq 1 15); do
        if curl -s http://localhost:8501 >/dev/null 2>&1; then
            log "  ✅ Frontend ready (${i}x2s)"
            break
        fi
        sleep 2
        [ $i -eq 15 ] && { log "  ❌ Frontend failed! Check: tail -20 ${LOG_DIR}/streamlit.log"; exit 1; }
    done
else
    log "  ✅ Frontend already running"
fi

# ============================================================
# FINAL STATUS
# ============================================================
echo ""
echo "========================================"
echo "=== ALL INTEGRATED SERVICES RUNNING ==="
echo "========================================"
echo ""
curl -s http://localhost:11434/api/tags >/dev/null && echo "✅ Ollama   → :11434" || echo "❌ Ollama   → :11434 FAILED"
curl -s http://localhost:8188/system_stats >/dev/null && echo "✅ ComfyUI  → :8188"  || echo "❌ ComfyUI  → :8188 FAILED"
curl -s http://localhost:8000/health >/dev/null && echo "✅ Queue API→ :8000"  || echo "❌ Queue API→ :8000 FAILED"
curl -s http://localhost:8501 >/dev/null && echo "✅ Frontend → :8501"  || echo "❌ Frontend → :8501 FAILED"
echo ""
echo "⚠️  MAKE SURE these ports are exposed in RunPod HTTP Services:"
echo "    11434 (Ollama) | 8188 (ComfyUI) | 8000 (Queue API) | 8501 (Frontend)"
echo ""
echo "Logs: ${LOG_DIR}/{ollama,comfyui,queue_api,streamlit}.log"
echo ""

# Keep alive
if [ -t 0 ]; then
    log "Press Ctrl+C to stop..."
    wait
fi
