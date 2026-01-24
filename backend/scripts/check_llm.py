
import os
import requests
import sys

def check_ollama_status():
    ollama_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    print(f"Checking Ollama at: {ollama_url}")
    
    try:
        # Check basic connectivity
        resp = requests.get(f"{ollama_url}/api/tags")
        if resp.status_code == 200:
            models = resp.json().get("models", [])
            print(f"[OK] Ollama is online. Found {len(models)} models.")
            
            model_names = [m['name'] for m in models]
            print(f"Available models: {', '.join(model_names)}")
            
            target_model = "gpt-oss:120b-cloud"  # Based on config scan
            # Handle tag variations (e.g., gpt-oss:120b-cloud vs gpt-oss:120b-cloud-latest)
            found = any(target_model in m for m in model_names)
            
            if found:
                print(f"[OK] Required model '{target_model}' is present.")
            else:
                print(f"[WARN] Configured model '{target_model}' NOT found in Ollama list.")
                print("       Please run: ollama pull gpt-oss:120b-cloud")
        else:
            print(f"[FAIL] Ollama returned status {resp.status_code}")
            
    except requests.exceptions.ConnectionError:
        print(f"[FAIL] Could not connect to Ollama at {ollama_url}. Is it running?")
        print("       If running in Docker, ensure internal networking is correct.")

if __name__ == "__main__":
    check_ollama_status()
