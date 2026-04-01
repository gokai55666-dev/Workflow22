#!/bin/bash
# status.sh - Check Girlbot service status

echo "🔍 Girlbot System Status"
echo "========================"
echo "$(date)"
echo ""

# Check services
check_service() {
    local name=$1
    local url=$2
    local port=$3

    if curl -s "$url" > /dev/null 2>&1; then
        echo "✅ $name (port $port): Running"
        return 0
    else
        echo "❌ $name (port $port): Down"
        return 1
    fi
}

check_service "Ollama" "http://localhost:11434/api/tags" "11434"
check_service "ComfyUI" "http://localhost:8188/system_stats" "8188"
check_service "Queue API" "http://localhost:8000/health" "8000"
check_service "Frontend" "http://localhost:8501" "8501"

echo ""
echo "📊 Resource Usage:"
echo "-----------------"

# GPU
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits 2>/dev/null | while IFS=',' read -r util mem_used mem_total; do
        echo "GPU: ${util}% util | VRAM: ${mem_used}/${mem_total} MB"
    done
else
    echo "GPU: nvidia-smi not available"
fi

# Disk
df -h /workspace 2>/dev/null | grep -v Filesystem | awk '{print "Disk: "$3"/"$2" ("$5" used)"}'

# Memory
free -h 2>/dev/null | grep Mem | awk '{print "RAM: "$3"/"$2}'

echo ""
echo "📁 Recent Logs:"
echo "--------------"
if [ -d "/workspace/logs" ]; then
    ls -lt /workspace/logs 2>/dev/null | head -6 | tail -5 | awk '{print "  "$9" ("$5")"}'
else
    echo "  No logs directory"
fi

echo ""
echo "🖼️  Recent Generations:"
echo "----------------------"
if [ -d "/workspace/ComfyUI/output" ]; then
    ls -lt /workspace/ComfyUI/output 2>/dev/null | head -6 | tail -5 | awk '{print "  "$9}'
else
    echo "  No output directory"
fi

echo ""
echo "🔧 Quick Actions:"
echo "----------------"
echo "Start:  bash /workspace/girlbot/launch.sh"
echo "Stop:   bash /workspace/girlbot/stop.sh"
echo "Logs:   tail -f /workspace/logs/*.log"
