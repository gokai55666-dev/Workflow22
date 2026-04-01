python
#!/usr/bin/env python3
import requests
import json
import re
from comfyui_llm_bridge import ComfyUIController

class LLMComfyUIAgent:
    def __init__(self, ollama_url="http://localhost:11434", comfy_url="http://localhost:8188"):
        self.ollama_url = ollama_url
        self.comfy = ComfyUIController(comfy_url)
        self.character_persona = None
        self.conversation_history = []
        
    def set_persona(self, description):
        """Set the AI's character persona"""
        self.character_persona = description
        print(f"✓ Persona set: {description[:100]}...")
    
    def chat(self, user_message, model="llama3.2"):
        """Chat with the LLM and execute ComfyUI commands"""
        
        # Add to history
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # Create system prompt
        system_prompt = f"""You are an AI character with this personality: {self.character_persona}

You have the ability to generate images using ComfyUI. When the user wants to generate an image, respond with:
[GENERATE: prompt description | width | height | steps]

If you need to list available models, use:
[LIST_MODELS]

Otherwise, respond naturally as your character.

Current available models: {len(self.comfy.available_models['checkpoints'])} checkpoints, {len(self.comfy.available_models['loras'])} LoRAs
"""
        
        # Call Ollama
        response = requests.post(
            f"{self.ollama_url}/api/generate",
            json={
                "model": model,
                "prompt": user_message,
                "system": system_prompt,
                "stream": False,
                "context": self.conversation_history
            }
        )
        
        ai_response = response.json()["response"]
        
        # Check for generation commands
        if "[GENERATE:" in ai_response:
            # Extract generation details
            match = re.search(r'\[GENERATE:\s*([^|]+)\|?(\d+)?\|?(\d+)?\|?(\d+)?\]', ai_response)
            if match:
                prompt = match.group(1).strip()
                width = int(match.group(2) or 512)
                height = int(match.group(3) or 512)
                steps = int(match.group(4) or 20)
                
                # Trigger ComfyUI generation
                result = self.comfy.generate_image(prompt, width=width, height=height, steps=steps)
                ai_response += f"\n\n✨ Image generation started! Prompt ID: {result.get('prompt_id', 'unknown')}"
        
        elif "[LIST_MODELS]" in ai_response:
            models = "\n".join(self.comfy.available_models['checkpoints'][:10])
            ai_response = f"Available models:\n{models}\n\nTotal: {len(self.comfy.available_models['checkpoints'])} checkpoints"
        
        # Add AI response to history
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response
    
    def interactive_mode(self):
        """Interactive chat mode"""
        print("\n" + "="*50)
        print("🤖 LLM ComfyUI Agent Ready!")
        print("="*50)
        print("Commands:")
        print("  /persona [description] - Set AI character")
        print("  /models - List available models")
        print("  /status - Check ComfyUI status")
        print("  /exit - Quit")
        print("="*50 + "\n")
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if user_input.startswith("/"):
                    cmd = user_input[1:].lower()
                    if cmd == "exit":
                        break
                    elif cmd == "models":
                        print(f"\nCheckpoints ({len(self.comfy.available_models['checkpoints'])}):")
                        for m in self.comfy.available_models['checkpoints'][:10]:
                            print(f"  - {m}")
                        if len(self.comfy.available_models['loras']) > 0:
                            print(f"\nLoRAs ({len(self.comfy.available_models['loras'])}):")
                            for l in self.comfy.available_models['loras'][:5]:
                                print(f"  - {l}")
                        continue
                    elif cmd.startswith("persona"):
                        persona_desc = user_input[9:].strip()
                        if persona_desc:
                            self.set_persona(persona_desc)
                        continue
                    elif cmd == "status":
                        try:
                            response = requests.get(f"{self.comfy.comfy_url}/system_stats")
                            if response.status_code == 200:
                                print("✅ ComfyUI is running")
                            else:
                                print("⚠️ ComfyUI responded but with status:", response.status_code)
                        except:
                            print("❌ Cannot connect to ComfyUI")
                        continue
                
                if not user_input:
                    continue
                
                # Send to AI
                print("AI: ", end="", flush=True)
                response = self.chat(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\nGoodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")

# Run the agent
if __name__ == "__main__":
    agent = LLMComfyUIAgent()
    
    # Set default persona
    agent.set_persona(
        "You are a creative AI assistant who specializes in generating amazing images and videos. "
        "You're enthusiastic, artistic, and love helping users bring their ideas to life. "
        "You understand composition, lighting, and artistic styles. "
        "When suggesting image generation, you provide detailed prompts with artistic guidance."
    )
    
    agent.interactive_mode()
