"""
Batch test to find a working Hugging Face model on the new router endpoints.
Run: python test_hf_router.py
"""
import asyncio
import httpx
from backend.config import settings

async def test_url(client, url, payload, label):
    try:
        headers = {
            "Authorization": f"Bearer {settings.HF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        res = await client.post(url, json=payload, headers=headers, timeout=15.0)
        print(f"  [{res.status_code}] {label}")
        if res.status_code == 200:
            print(f"  RESPONSE SNIPPET: {res.text[:120]}")
            return True
        else:
            print(f"  BODY: {res.text[:80]}")
            return False
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

async def main():
    print(f"HF Token present: {bool(settings.HF_API_TOKEN)}\n")

    # Models to try  
    models = [
        "Qwen/Qwen2.5-7B-Instruct",
        "Qwen/Qwen2.5-72B-Instruct",
        "meta-llama/Llama-3.2-3B-Instruct",
        "mistralai/Mistral-7B-Instruct-v0.3",
        "HuggingFaceH4/zephyr-7b-beta",
        "TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        "microsoft/Phi-3.5-mini-instruct",
        "google/gemma-2-2b-it",
    ]

    chat_payload = {
        "messages": [{"role": "user", "content": "Say hello"}],
        "max_tokens": 20,
        "stream": False
    }
    
    text_payload = {
        "inputs": "Hello!",
        "parameters": {"max_new_tokens": 20}
    }

    async with httpx.AsyncClient() as client:
        for model in models:
            print(f"\n=== {model} ===")
            
            # Try router chat completions
            url_chat = f"https://router.huggingface.co/hf-inference/models/{model}/v1/chat/completions"
            if await test_url(client, url_chat, chat_payload, "router/chat"):
                print(f"\n✅ WORKING: {model} via router/chat/completions")
                return
            
            # Try router standard text
            url_text = f"https://router.huggingface.co/hf-inference/models/{model}"
            if await test_url(client, url_text, text_payload, "router/text"):
                print(f"\n✅ WORKING: {model} via router/text")
                return

    print("\n❌ No models worked. You may need a HF Pro subscription.")

if __name__ == "__main__":
    asyncio.run(main())
