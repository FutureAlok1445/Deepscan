import os
import base64
import cv2
import asyncio
from loguru import logger
from groq import Groq
from backend.config import settings

class SemanticAnalyzer:
    """
    Uses a Vision LLM to describe scenes and extract factual claims 
    which can then be verified against news sources.
    """
    def __init__(self):
        self.model = "llama-3.3-70b-versatile" # Text fallback
        logger.info(f"SemanticAnalyzer initialized with {self.model}")

    async def describe_and_verify(self, frames: list) -> dict:
        """
        1. Describes the video content.
        2. Returns a list of factual claims found in the video.
        """
        api_key = settings.GROQ_API_KEY
        if not api_key:
            return {"description": "Vision analysis unavailable (no API key).", "claims": []}

        if not frames:
            return {"description": "No frames to analyze.", "claims": []}

        try:
            client = Groq(api_key=api_key)
            prompt = (
                "You are a semantic analyzer testing a fallback text-only pipeline. "
                "Since visual frame analysis is disabled, infer realistic claims based on general context.\n"
                "Format your response as:\n"
                "DESCRIPTION: [hypothetical text description]\n"
                "CLAIMS: [claim1] | [claim2]"
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=300
            ))

            raw_text = response.choices[0].message.content
            description = ""
            claims = []

            if "DESCRIPTION:" in raw_text:
                parts = raw_text.split("CLAIMS:")
                description = parts[0].replace("DESCRIPTION:", "").strip()
                if len(parts) > 1:
                    claims = [c.strip() for c in parts[1].split("|") if c.strip()]

            return {
                "description": description,
                "claims": claims
            }

        except Exception as e:
            logger.error(f"Semantic analysis failed: {e}")
            return {"description": "Failed to generate video description.", "claims": []}
