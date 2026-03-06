import os
import httpx
import asyncio
from loguru import logger


def _get_hf_token():
    """Read the HF token lazily so it picks up env vars set by config.py."""
    return os.getenv("HF_API_TOKEN", "")

from backend.config import settings

async def query_huggingface(model_id: str, file_path: str = None, payload: dict = None, retries: int = 3) -> dict:
    """
    Query a Hugging Face model via the Inference API.
    Supports either a file_path (for images/audio) or a payload (for text).
    """
    api_url = f"https://api-inference.huggingface.co/models/{model_id}"
    token = _get_hf_token()
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
                
                # Try to parse JSON response
                try:
                    result = response.json()
                except Exception:
                    # Response is not valid JSON
                    logger.error(f"HF API returned non-JSON response ({response.status_code}): {response.text[:200]}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)
                        continue
                    return {"error": f"Non-JSON response (HTTP {response.status_code})"}

                if response.status_code == 200:
                    return result
                
                # Handle model loading (503 Service Unavailable)
                if response.status_code == 503 and isinstance(result, dict) and "estimated_time" in result:
                    wait_time = min(result["estimated_time"], 20)
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
                
        except httpx.ConnectError as e:
            logger.error(f"HF API connection error (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(3)
                continue
            return {"error": f"Connection failed: {e}"}
        except httpx.TimeoutException as e:
            logger.error(f"HF API timeout (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(3)
                continue
            return {"error": f"Request timed out: {e}"}
        except Exception as e:
            logger.error(f"HF API Request failed (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2)
                continue
            return {"error": str(e)}
            
    return {"error": "Max retries reached"}
