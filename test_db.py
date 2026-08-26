import os
from dotenv import load_dotenv
from langchain_nvidia_ai_endpoints import ChatNVIDIA

load_dotenv(override=True)

print("Hunting for a stable, active NVIDIA model...")
available_models = ChatNVIDIA.get_available_models()

for m in available_models:
    model_name = m.id
    # Filter for standard instruct models
    if "instruct" in model_name.lower():
        try:
            print(f"Testing: {model_name} ...")
            # max_retries=0 ensures it fails fast if the endpoint is dead
            llm = ChatNVIDIA(model=model_name, max_retries=0, timeout=10)
            
            # The actual physical test
            response = llm.invoke("Say the word 'Hello'")
            
            print(f"\n✅ SUCCESS! The NVIDIA backend is working for this model.")
            print(f"👉 COPY THIS EXACT STRING: \"{model_name}\"")
            print(f"🤖 Response received: {response.content}")
            break # Stop checking once we find one that works!
            
        except Exception:
            # Silently ignore 404s, 410s, and function ID errors and try the next one
            continue