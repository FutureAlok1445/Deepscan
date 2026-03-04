import os
import httpx
from loguru import logger

# Simple translation with fallback
BASIC_HINDI = {
    "AUTHENTIC": "प्रामाणिक",
    "UNCERTAIN": "अनिश्चित",
    "LIKELY_FAKE": "संभवतः नकली",
    "DEFINITELY_FAKE": "निश्चित रूप से नकली",
    "Score": "स्कोर",
    "Analysis complete": "विश्लेषण पूर्ण",
    "Deepfake detected": "डीपफेक पाया गया",
    "No manipulation found": "कोई हेरफेर नहीं मिला",
}


async def translate_text(text: str, target: str = "hi") -> str:
    """Translate text to target language. Uses Google Translate API if
    available, otherwise returns Hindi keyword substitution or original text."""
    if target == "en":
        return text

    api_key = os.getenv("GOOGLE_TRANSLATE_KEY", "")

    # Try Google Translate API
    if api_key:
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(
                    "https://translation.googleapis.com/language/translate/v2",
                    params={"key": api_key},
                    json={"q": text, "target": target, "format": "text"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    return data["data"]["translations"][0]["translatedText"]
        except Exception as e:
            logger.warning(f"Google Translate failed: {e}")

    # Fallback: basic Hindi keyword replacement
    if target == "hi":
        result = text
        for eng, hin in BASIC_HINDI.items():
            result = result.replace(eng, hin)
        return result

    return text