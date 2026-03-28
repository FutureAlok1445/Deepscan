import os
import httpx
import asyncio
from loguru import logger

from backend.config import settings


async def query_huggingface(model_id: str, file_path: str = None, payload: dict = None, retries: int = 3) -> dict:
    """
    Query a Hugging Face model via the Inference API.
    Supports either a file_path (for images/audio) or a payload (for text).
    Returns dict with results on success, or {"error": "..."} on failure.
    """
    token = settings.HF_API_TOKEN or os.getenv("HF_API_TOKEN", "")

    if model_id.startswith("http"):
        api_url = model_id
    else:
        api_url = f"https://router.huggingface.co/hf-inference/models/{model_id}"

    headers = {"Authorization": f"Bearer {token}"} if token else {}

    if not token:
        logger.warning("HF_API_TOKEN not set. Inference API may fail or be heavily rate-limited.")

    # Read file data if file_path is provided
    data = None
    if file_path:
        try:
            with open(file_path, "rb") as f:
                data = f.read()
        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            return {"error": f"Failed to read file: {e}"}

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
                    logger.error(f"HF API non-JSON ({response.status_code}): {response.text[:200]}")
                    if attempt < retries - 1:
                        await asyncio.sleep(2)
                        continue
                    return {"error": f"Non-JSON response (HTTP {response.status_code})"}

                # Success
                if response.status_code == 200:
                    return result

                # Model is loading (503) — wait and retry
                if response.status_code == 503 and isinstance(result, dict) and "estimated_time" in result:
                    wait_time = min(float(result["estimated_time"]), 20)
                    logger.info(f"Model {model_id} loading. Waiting {wait_time:.0f}s (attempt {attempt+1}/{retries})")
                    await asyncio.sleep(wait_time)
                    continue

                # Other error
                logger.error(f"HF API error ({response.status_code}): {str(result)[:200]}")
                if attempt < retries - 1:
                    await asyncio.sleep(2)
                    continue
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
            logger.error(f"HF API request failed (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(2)
                continue
            return {"error": str(e)}

    return {"error": "Max retries reached"}
