import os
import httpx
import asyncio
from loguru import logger
from backend.config import settings

async def query_huggingface(model_id: str, file_path: str = None, payload: dict = None, retries: int = 3) -> dict:
    """
    Query a Hugging Face model via the Inference API.
    Supports either a file_path (for images/audio) or a payload (for text).
    """
    token = settings.HF_API_TOKEN
    
    # Use HF Router if ID is passed, else use the raw URL if provided
    if model_id.startswith("http"):
        api_url = model_id
    else:
        api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"
        
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    
    if not token:
        logger.warning("HF_API_TOKEN not set. Inference API may fail or be heavily rate-limited.")

    data = None
    if file_path:
        with open(file_path, "rb") as f:
            data = f.read()
    
    for attempt in range(retries):
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                if data:
                    response = await client.post(api_url, headers=headers, content=data)
                else:
                    response = await client.post(api_url, headers=headers, json=payload)
                
                # Check if content type is JSON before parsing
                if "application/json" not in response.headers.get("Content-Type", ""):
                    logger.error(f"HF API returned non-JSON response ({response.status_code}): {response.text[:200]}")
                    return {"error": "Non-JSON response from API", "status_code": response.status_code}

                result = response.json()
                if response.status_code == 200:
                    return result
                # Handle model loading (503 Service Unavailable)
                if response.status_code == 503 and "estimated_time" in result:
                    wait_time = min(result["estimated_time"], 10)
                    logger.info(f"Model {model_id} is loading. Waiting {wait_time}s (Attempt {attempt+1}/{retries})...")
                    await asyncio.sleep(wait_time)
                    continue
                
                logger.error(f"HF API Error ({response.status_code}): {result}")
                return {"error": str(result), "status_code": response.status_code}
                
        except Exception as e:
            logger.error(f"HF API Request failed: {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2)
                continue
            return {"error": str(e)}
            
    return {"error": "Max retries reached"}
