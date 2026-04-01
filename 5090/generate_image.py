import json
import subprocess
import os

# Paths
PROMPT_FILE = "/workspace/LLM_Comfy_Interface/prompt_queue.json"
RESULT_FILE = "/workspace/LLM_Comfy_Interface/result_queue.json"
OUTPUT_DIR = "/workspace/LLM_Comfy_Interface/outputs"

os.makedirs(OUTPUT_DIR, exist_ok=True)

# Load prompt
with open(PROMPT_FILE) as f:
    data = json.load(f)

prompt = data.get("prompt", "")
negative = data.get("negative_prompt", "")
model = data.get("model", "dreamshaper_8")
loras = data.get("loras", [])
steps = str(data.get("steps", 30))
cfg = str(data.get("cfg", 7))

# Build command
cmd = [
    "python3", "/workspace/ComfyUI/main.py",
    "--prompt", prompt,
    "--negative_prompt", negative,
    "--checkpoint", f"/workspace/ComfyUI/models/checkpoints/{model}",
    "--steps", steps,
    "--cfg", cfg,
    "--resolution", "1024", "1024",  # can be changed dynamically
    "--outdir", OUTPUT_DIR
]

# Attach LoRAs
for lora in loras:
    lora_path = f"/workspace/ComfyUI/models/loras/{lora}.safetensors"
    if os.path.exists(lora_path):
        cmd.extend(["--lora", lora_path])

# Run ComfyUI generation
subprocess.run(cmd)

# Write result
last_image = max(
    [os.path.join(OUTPUT_DIR, f) for f in os.listdir(OUTPUT_DIR)],
    key=os.path.getctime
)

with open(RESULT_FILE, "w") as f:
    json.dump({"output_image": last_image, "status": "ready"}, f)

print(f"Image saved: {last_image}")
