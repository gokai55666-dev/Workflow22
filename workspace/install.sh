#!/bin/bash

apt update && apt install -y python3-pip git wget
pip install fastapi uvicorn aiohttp streamlit

# install ComfyUI if missing
cd /workspace
[ ! -d "ComfyUI" ] && git clone https://github.com/comfyanonymous/ComfyUI

echo "✅ INSTALL COMPLETE"