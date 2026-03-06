import asyncio
from backend.config import settings
from backend.utils.hf_api import query_huggingface

async def test_all():
    token = settings.HF_API_TOKEN
    print(f"Token present: {bool(token)}")
    
    models = [
        "Qwen/Qwen2.5-72B-Instruct",
        "Qwen/Qwen2.5-7B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "HuggingFaceH4/zephyr-7b-beta",
        "meta-llama/Llama-3.2-3B-Instruct"
    ]
    
    payload_chat = {
        "messages": [{"role": "user", "content": "Hello"}],
        "max_tokens": 10
    }
    
    payload_text = {
        "inputs": "Hello",
        "parameters": {"max_new_tokens": 10}
    }
    
    for model in models:
        print(f"\n--- Testing {model} ---")
        
        # Test 1: Router v1/chat
        url1 = f"https://api-inference.huggingface.co/models/{model}/v1/chat/completions"
        print("Testing:", url1)
        res1 = await query_huggingface(url1, payload=payload_chat, retries=1)
        print("Result:", res1.get('status_code', 'Success') if isinstance(res1, dict) and 'error' in res1 else 'Success')
        
        if isinstance(res1, dict) and 'error' not in res1:
            print("WORKING MODEL FOUND:", model, "Chat API")
            return
            
        # Test 2: Standard Router
        url3 = f"https://router.huggingface.co/hf-inference/models/{model}"
        print("Testing:", url3)
        res3 = await query_huggingface(url3, payload=payload_text, retries=1)
        print("Result:", res3.get('status_code', 'Success') if isinstance(res3, dict) and 'error' in res3 else 'Success')
        
        if isinstance(res3, list) or (isinstance(res3, dict) and 'error' not in res3):
             print("WORKING MODEL FOUND:", model, "Standard API")
             return

if __name__ == "__main__":
    asyncio.run(test_all())
