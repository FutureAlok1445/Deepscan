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
        self.model = "llama-3.2-11b-vision-preview" # Groq vision model
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
            # We only send 1-2 key frames to minimize token usage
            key_frame = frames[len(frames)//2]
            _, buffer = cv2.imencode(".jpg", key_frame, [int(cv2.IMWRITE_JPEG_QUALITY), 60])
            b64_image = base64.b64encode(buffer).decode("utf-8")

            client = Groq(api_key=api_key)
            prompt = (
                "Describe exactly what is happening in this image. Who is shown? Where are they? What are they doing?\n"
                "Then, extract 1-3 specific factual claims (e.g. 'Elon Musk is talking about Mars at a rally in Texas').\n"
                "Format your response as:\n"
                "DESCRIPTION: <description>\n"
                "CLAIMS: <claim1> | <claim2>"
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(None, lambda: client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}
                            }
                        ]
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
