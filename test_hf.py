import asyncio
from backend.config import settings
from backend.utils.hf_api import query_huggingface

async def test_hf():
    print(f"Token present: {bool(settings.HF_API_TOKEN)}")
    model_url = "https://router.huggingface.co/hf-inference/models/mistralai/Mistral-7B-Instruct-v0.2/v1/chat/completions"
    payload = {
        "model": "mistralai/Mistral-7B-Instruct-v0.2",
        "messages": [{"role": "user", "content": "Test prompt"}],
        "max_tokens": 100
    }
    res = await query_huggingface(model_url, payload=payload)
    print("HF RESPONSE:", res)

if __name__ == "__main__":
    asyncio.run(test_hf())
