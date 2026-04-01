"""
queue_api.py - FastAPI Queue Layer for Girlbot
RunPod Optimized - Integrates with testv1
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import asyncio
import json
import os
import sys
import uuid
import requests
import random

app = FastAPI(title="Girlbot Queue API", version="2.0.0")

# Queue storage
job_queue = asyncio.Queue()
job_results = {}
job_status = {}

class GenerateRequest(BaseModel):
    prompt: str
    mode: str = "basic"
    seed: int = -1

@app.post("/gen")
async def submit_job(request: GenerateRequest):
    """Submit generation job to queue"""
    job_id = str(uuid.uuid4())[:8]
    await job_queue.put((job_id, request.dict()))
    job_status[job_id] = "pending"
    return {
        "job_id": job_id,
        "status": "queued",
        "position": job_queue.qsize(),
        "message": "Job queued successfully"
    }

@app.get("/res/{job_id}")
async def get_result(job_id: str):
    """Get job result"""
    if job_id in job_results:
        return job_results[job_id]
    if job_id in job_status:
        return {"status": job_status[job_id], "file": None}
    raise HTTPException(status_code=404, detail="Job not found")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "queue_size": job_queue.qsize(),
        "active_jobs": len([s for s in job_status.values() if s == "processing"]),
        "completed": len([s for s in job_status.values() if s == "done"])
    }

def load_config():
    """Load config from testv1 location"""
    config_path = "/workspace/system/config.json"
    default = {
        "services": {"comfyui": {"url": "http://localhost:8188"}},
        "storage": {"workflows": "/workspace/girlbot/workflows", "output": "/workspace/ComfyUI/output"}
    }
    if os.path.exists(config_path):
        with open(config_path) as f:
            return json.load(f)
    return default

def construct_workflow(prompt: str, mode: str = "basic", seed: int = None):
    """Build workflow - compatible with testv1 logic"""
    if seed is None or seed < 0:
        seed = random.randint(1, 2**31)

    cfg = load_config()
    workflow_dir = cfg["storage"]["workflows"]

    # Try to load template
    template_path = os.path.join(workflow_dir, f"text2img_{mode}.json")
    if not os.path.exists(template_path):
        template_path = os.path.join(workflow_dir, "text2img_basic.json")

    if os.path.exists(template_path):
        with open(template_path) as f:
            wf = json.load(f)
        # Update prompt and seed
        for node in wf.values():
            if node.get("class_type") == "CLIPTextEncode":
                if "text" in node.get("inputs", {}):
                    node["inputs"]["text"] = prompt
            if node.get("class_type") == "KSampler":
                node["inputs"]["seed"] = seed
        return wf, seed

    # Fallback inline workflow
    return {
        "1": {"inputs": {"ckpt_name": "dreamshaper_8.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "2": {"inputs": {"text": prompt, "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "3": {"inputs": {"text": "blurry, bad, low quality", "clip": ["1", 1]}, "class_type": "CLIPTextEncode"},
        "4": {"inputs": {"width": 1024, "height": 1024, "batch_size": 1}, "class_type": "EmptyLatentImage"},
        "5": {"inputs": {"seed": seed, "steps": 30, "cfg": 7, "sampler_name": "euler", "scheduler": "normal",
                      "model": ["1", 0], "positive": ["2", 0], "negative": ["3", 0], "latent_image": ["4", 0]},
              "class_type": "KSampler"},
        "6": {"inputs": {"samples": ["5", 0], "vae": ["1", 2]}, "class_type": "VAEDecode"},
        "7": {"inputs": {"filename_prefix": "girlbot", "images": ["6", 0]}, "class_type": "SaveImage"}
    }, seed

async def process_queue():
    """Background worker"""
    cfg = load_config()
    comfy_url = cfg["services"]["comfyui"]["url"]

    while True:
        job_id, data = await job_queue.get()
        job_status[job_id] = "processing"

        try:
            prompt = data["prompt"]
            mode = data.get("mode", "basic")
            seed = data.get("seed", -1)

            # Build workflow
            wf, used_seed = construct_workflow(prompt, mode, seed)

            # Submit to ComfyUI
            response = requests.post(f"{comfy_url}/prompt", json={"prompt": wf}, timeout=10)
            response.raise_for_status()
            prompt_id = response.json().get("prompt_id")

            # Poll for result
            for _ in range(150):  # 5 min max
                await asyncio.sleep(2)
                try:
                    r = requests.get(f"{comfy_url}/history/{prompt_id}", timeout=5)
                    history = r.json()

                    if prompt_id in history:
                        outputs = history[prompt_id].get("outputs", {})
                        for node_out in outputs.values():
                            if "images" in node_out:
                                filename = node_out["images"][0]["filename"]
                                job_results[job_id] = {
                                    "status": "done",
                                    "file": filename,
                                    "seed": used_seed,
                                    "view_url": f"{comfy_url}/view?filename={filename}&type=output"
                                }
                                job_status[job_id] = "done"
                                break
                        break
                except:
                    continue
            else:
                job_results[job_id] = {"status": "error", "message": "Timeout"}
                job_status[job_id] = "error"

        except Exception as e:
            job_results[job_id] = {"status": "error", "message": str(e)}
            job_status[job_id] = "error"

        job_queue.task_done()

@app.on_event("startup")
async def startup():
    asyncio.create_task(process_queue())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
