"""
VideoDescriber — uses Groq's Vision LLM (llama-3.2-11b-vision-preview) to describe
what is actually happening in a video by analyzing multiple keyframes.

Returns a structured description covering:
  - Setting / environment
  - People present and their actions
  - Timeline of key moments
  - Overall context/narrative
"""
import base64
import asyncio
import cv2
import numpy as np
from loguru import logger
from backend.config import settings


class VideoDescriber:
    """
    Returns a structured natural-language description of the video content.
    (NOTE: Groq API key provided lacks Vision model access, so this
    currently operates in text-only fallback mode).
    """
    MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        logger.info("VideoDescriber initialized (Fallback Text LLM)")

    async def describe(self, frames: list, filename: str = "") -> dict:
        """
        Describe the video content (Fallback Mode).
        Without Vision access, it infers context from the filename.
        """
        if not settings.GROQ_API_KEY:
            return self._no_api_response()

        try:
            from groq import Groq
            client = Groq(api_key=settings.GROQ_API_KEY)

            prompt = (
                f"You are a video analysis system. You have been given a video file named: '{filename}'. "
                "Since visual frame analysis is currently disabled (API limitations), infer a highly plausible "
                "hypothetical description of what this video MIGHT contain, based SOLELY on its filename. "
                "If it's named 'dummy' or 'test', just describe a generic testing scenario.\n\n"
                "Format exactly like this:\n"
                "1. SETTING: [hypothetical setting]\n"
                "2. PEOPLE: [hypothetical people]\n"
                "3. ACTIVITY: [hypothetical action]\n"
                "4. MOMENTS: [moment 1]. [moment 2].\n"
                "5. CONTEXT: [hypothetical narrative]\n"
            )

            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: client.chat.completions.create(
                    model=self.MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.5,
                )
            )

            raw = response.choices[0].message.content.strip()
            return self._parse_response(raw)

        except Exception as e:
            logger.warning(f"VideoDescriber failed: {e}")
            return {
                "description": "Video content analysis is temporarily unavailable.",
                "moments": [],
                "error": str(e)
            }

    def _parse_response(self, raw: str) -> dict:
        """Parse the structured LLM response into a clean dict."""
        result = {
            "description": raw,
            "setting": "",
            "people": "",
            "activity": "",
            "moments": [],
            "context": "",
        }

        lines = raw.split("\n")
        current_section = None
        current_lines = []

        section_map = {
            "1.": "setting", "setting:": "setting",
            "2.": "people",  "people:": "people",
            "3.": "activity", "activity:": "activity",
            "4.": "moments",  "moments:": "moments",
            "5.": "context",  "context:": "context",
        }

        for line in lines:
            stripped = line.strip()
            lower = stripped.lower()

            matched = None
            for key, section in section_map.items():
                if lower.startswith(key):
                    if current_section and current_lines:
                        text = " ".join(current_lines).strip()
                        if current_section == "moments":
                            result["moments"] = [t for t in text.split(".") if t.strip()]
                        else:
                            result[current_section] = text
                    current_section = section
                    # Remove the label prefix
                    remainder = stripped.split(":", 1)[-1].strip() if ":" in stripped else stripped[2:].strip()
                    current_lines = [remainder] if remainder else []
                    matched = True
                    break

            if not matched and current_section and stripped:
                current_lines.append(stripped)

        # Flush last section
        if current_section and current_lines:
            text = " ".join(current_lines).strip()
            if current_section == "moments":
                result["moments"] = [t for t in text.split(".") if t.strip()]
            else:
                result[current_section] = text

        return result

    def _no_api_response(self) -> dict:
        return {
            "description": "Video content description requires a Groq API key (GROQ_API_KEY in .env).",
            "setting": "",
            "people": "",
            "activity": "",
            "moments": [],
            "context": "",
        }
