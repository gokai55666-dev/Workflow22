#!/bin/bash
# ============================================================
# GIRL BOT AI - INTEGRATED MASTER INSTALL (integrated_master_install.sh)
# Combines testv1 setup with Workflow22 queue API and frontend.
# Safe to re-run.
# ============================================================

set -e
echo "========================================================"
echo "  GIRL BOT AI STUDIO - INTEGRATED MASTER INSTALL"
echo "========================================================"
cd /workspace

# Helper function for logging
log() { echo "[$(date +%H:%M:%S)] $1"; }

# ── 1. Run testv1 Master-install.sh for base setup ────────────────────────
# This handles GPU checks, system packages, PyTorch (cu128), Ollama, ComfyUI,
# and sets up the /workspace/girlbot directory with base config and workflows.
log "[1/3] Running testv1 Master-install.sh for base setup..."
# Ensure testv1 repository is cloned. If not, clone it first.
if [ ! -d "/home/ubuntu/testv1" ]; then
    log "Cloning testv1 repository..."
    git clone https://github.com/gokai55666-dev/testv1.git /home/ubuntu/testv1
fi
/home/ubuntu/testv1/RTX-5090/Master-install.sh
log "✅ testv1 base setup complete."

# ── 2. Integrate Workflow22 components ────────────────────────────────────
log "[2/3] Integrating Workflow22 components..."

# Ensure Workflow22 repository is cloned. If not, clone it first.
if [ ! -d "/home/ubuntu/Workflow22" ]; then
    log "Cloning Workflow22 repository..."
    git clone https://github.com/gokai55666-dev/Workflow22.git /home/ubuntu/Workflow22
fi

# Copy Workflow22 queue API and related files to /workspace/girlbot
cp /home/ubuntu/Workflow22/workspace/girlbot/app_queue.py /workspace/girlbot/queue_api.py
cp /home/ubuntu/Workflow22/workspace/girlbot/comfy_client.py /workspace/girlbot/comfy_client.py
cp /home/ubuntu/Workflow22/workspace/girlbot/workflow.py /workspace/girlbot/workflow.py

# Install additional Python dependencies for the queue API
log "Installing additional Python dependencies for Queue API..."
pip install -q fastapi uvicorn aiohttp --break-system-packages

# Modify Workflow22's workflow.py to use the correct model name from testv1
# (v1-5-pruned-emaonly.safetensors instead of dreamshaper_8.safetensors)
log "Adapting Workflow22 workflow.py to use testv1 model..."
sed -i 's/dreamshaper_8.safetensors/v1-5-pruned-emaonly.safetensors/g' /workspace/girlbot/workflow.py

log "✅ Workflow22 components integrated and adapted."

# ── 3. Prepare for Frontend Replacement ───────────────────────────────────
log "[3/3] Preparing for frontend replacement..."

# Stop the old streamlit process launched by testv1 Master-install.sh
pkill -f "streamlit run /workspace/girlbot/app.py" 2>/dev/null || true
sleep 2

log "⚠️ Frontend replacement pending. You will need to copy the modified_app.py content into /workspace/girlbot/app.py in the next step."

# ── Final summary ─────────────────────────────────────────────────────────
echo ""
echo "========================================================"
echo "  INTEGRATED INSTALL COMPLETE (Manual step required)"
echo "========================================================"
echo ""
echo "To complete the setup, you need to replace /workspace/girlbot/app.py with the provided modified version."
echo "Then, run the integrated launch script: bash /home/ubuntu/integrated_launch.sh"
echo ""
