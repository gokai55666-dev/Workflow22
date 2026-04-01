python
#!/usr/bin/env python3
import json
import requests
import time
import subprocess
import os
from datetime import datetime

class ComfyUIController:
    def __init__(self, comfy_url="http://127.0.0.1:8188"):
        self.comfy_url = comfy_url
        self.available_models = self.scan_models()
        
    def scan_models(self):
        """Scan available models in ComfyUI directories"""
        models = {
            "checkpoints": [],
            "loras": [],
            "vae": [],
            "embeddings": []
        }
        
        # Adjust these paths based on your ComfyUI setup
        comfy_paths = [
            "/workspace/ComfyUI/models",
            "/workspace/ConFlyUI/models", 
            "/workspace/ComfyUI/models/checkpoints"
        ]
        
        for base_path in comfy_paths:
            if os.path.exists(base_path):
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if file.endswith(('.safetensors', '.ckpt', '.pt')):
                            if 'lora' in root.lower():
                                models["loras"].append(file)
                            elif 'vae' in root.lower():
                                models["vae"].append(file)
                            elif 'embed' in root.lower():
                                models["embeddings"].append(file)
                            else:
                                models["checkpoints"].append(file)
        
        # Deduplicate
        for key in models:
            models[key] = list(set(models[key]))
        
        return models
    
    def get_workflow(self):
        """Get current workflow from ComfyUI"""
        try:
            response = requests.get(f"{self.comfy_url}/object_info")
            return response.json()
        except:
            return None
    
    def queue_prompt(self, prompt_workflow):
        """Queue a prompt to ComfyUI"""
        try:
            response = requests.post(
                f"{self.comfy_url}/prompt",
                json={"prompt": prompt_workflow}
            )
            return response.json()
        except Exception as e:
            return {"error": str(e)}
    
    def interrupt_current(self):
        """Stop current generation"""
        try:
            response = requests.post(f"{self.comfy_url}/interrupt")
            return response.status_code == 200
        except:
            return False
    
    def generate_image(self, prompt, negative_prompt="", width=512, height=512, steps=20, model=None):
        """Simple image generation - you'll need to adapt this to your actual workflow"""
        
        # This is a simplified workflow - replace with your actual node structure
        workflow = {
            "1": {
                "class_type": "CheckpointLoaderSimple",
                "inputs": {
                    "ckpt_name": model or (self.available_models["checkpoints"][0] if self.available_models["checkpoints"] else "model.safetensors")
                }
            },
            "2": {
                "class_type": "CLIPTextEncode",
                "inputs": {
                    "text": prompt,
                    "clip": ["1", 1]
                }
            },
            "3": {
                "class_type": "CLIPTextEncode", 
                "inputs": {
                    "text": negative_prompt,
                    "clip": ["1", 1]
                }
            },
            "4": {
                "class_type": "EmptyLatentImage",
                "inputs": {
                    "width": width,
                    "height": height,
                    "batch_size": 1
                }
            },
            "5": {
                "class_type": "KSampler",
                "inputs": {
                    "seed": int(time.time()),
                    "steps": steps,
                    "cfg": 7.5,
                    "sampler_name": "euler",
                    "scheduler": "normal",
                    "denoise": 1,
                    "model": ["1", 0],
                    "positive": ["2", 0],
                    "negative": ["3", 0],
                    "latent_image": ["4", 0]
                }
            },
            "6": {
                "class_type": "VAEDecode",
                "inputs": {
                    "samples": ["5", 0],
                    "vae": ["1", 2]
                }
            },
            "7": {
                "class_type": "SaveImage",
                "inputs": {
                    "filename_prefix": f"generated_{int(time.time())}",
                    "images": ["6", 0]
                }
            }
        }
        
        return self.queue_prompt(workflow)
    
    def load_lora(self, lora_name, model_strength=1.0, clip_strength=1.0):
        """Load a LoRA for generation"""
        # Implementation depends on your workflow structure
        pass

# Create controller instance
controller = ComfyUIController()

# Simple CLI for testing
if __name__ == "__main__":
    print("ComfyUI LLM Bridge Ready!")
    print(f"Available Models: {controller.available_models['checkpoints'][:5]}")
    
    while True:
        cmd = input("\nEnter command (generate/list/exit): ").strip()
        if cmd == "exit":
            break
        elif cmd == "list":
            print(f"Checkpoints: {controller.available_models['checkpoints']}")
            print(f"LoRAs: {controller.available_models['loras']}")
        elif cmd.startswith("generate"):
            prompt = cmd.replace("generate", "").strip()
            if prompt:
                result = controller.generate_image(prompt)
                print(f"Generation queued: {result}")
