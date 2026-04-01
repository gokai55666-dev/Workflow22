#!/bin/bash
# stop.sh - Stop all Girlbot services cleanly

echo "🛑 Stopping Girlbot services..."
echo "================================"

# Find and kill processes
for service in "ollama" "comfyui" "queue_api" "streamlit"; do
    pids=$(pgrep -f "$service" || true)
    if [ -n "$pids" ]; then
        echo "Stopping $service (PIDs: $pids)..."
        echo "$pids" | xargs kill -TERM 2>/dev/null || true
        sleep 2
        # Force kill if still running
        pids=$(pgrep -f "$service" || true)
        if [ -n "$pids" ]; then
            echo "$pids" | xargs kill -KILL 2>/dev/null || true
        fi
    else
        echo "$service: not running"
    fi
done

echo ""
echo "✅ All services stopped"
echo ""
echo "Port status:"
for port in 11434 8188 8000 8501; do
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "  Port $port: ❌ still in use"
    else
        echo "  Port $port: ✅ free"
    fi
done
