import os
import base64

import httpx
from loguru import logger


async def reverse_image_search(image_bytes: bytes) -> dict:
    """
    Call Google Vision API WEB_DETECTION asynchronously on image bytes.
    Returns simple dict safe for JSON response.
    """
    api_key = os.getenv("GOOGLE_VISION_API_KEY", "")
    if not api_key:
        return {
            "match_count": 0,
            "matched_urls": [],
            "best_guess_label": "Unknown",
            "verdict": "API key not set",
        }

    try:
        b64 = base64.b64encode(image_bytes).decode("utf-8")
        payload = {
            "requests": [
                {
                    "image": {"content": b64},
                    "features": [{"type": "WEB_DETECTION", "maxResults": 5}],
                }
            ]
        }
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"

        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json=payload, timeout=10.0)
            resp.raise_for_status()
            data = resp.json()

            web = data["responses"][0].get("webDetection", {})
            pages = web.get("pagesWithMatchingImages", [])
            guesses = web.get("bestGuessLabels", [])

            urls = [p.get("url", "") for p in pages[:5]]
            label = guesses[0].get("label", "Unknown") if guesses else "Unknown"

            return {
                "match_count": len(urls),
                "matched_urls": urls,
                "best_guess_label": label,
                "verdict": "Found online" if urls else "Possibly original",
            }
    except Exception as e:
        logger.error(f"Google Vision API error: {e}")
        return {
            "match_count": 0,
            "matched_urls": [],
            "best_guess_label": "Unknown",
            "verdict": "API error",
        }

