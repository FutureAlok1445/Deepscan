import os
import json
from loguru import logger
try:
    from anthropic import Anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

CLAUDE_PROMPT = """You are a forensic AI image analyst. Carefully examine this image and identify ALL regions that appear to be AI-generated, digitally manipulated, composited, or deepfaked.

For EACH suspicious region, define a polygon using 6-12 points with normalised coordinates (0.0 to 1.0, where [0,0] is top-left and [1,1] is bottom-right).

Respond ONLY with this exact JSON — no markdown, no extra text:
{
  "ai_score": <integer 0-100, overall probability image contains AI content>,
  "verdict": "<AUTHENTIC | POSSIBLY MANIPULATED | LIKELY AI | CONFIRMED AI>",
  "summary": "<2 sentences explaining what you found>",
  "regions": [
    {
      "label": "<what this region is, e.g. 'AI-generated background', 'deepfake face', 'composited element'>",
      "intensity": <0.0-1.0, how confident this region is AI>,
      "polygon": [[x1,y1],[x2,y2],[x3,y3],...]
    }
  ],
  "signals": [
    { "label": "Noise Consistency",     "status": "<detected|warning|clean>", "detail": "<1 sentence>" },
    { "label": "Lighting & Color Temp", "status": "<detected|warning|clean>", "detail": "<1 sentence>" },
    { "label": "Texture Artifacts",     "status": "<detected|warning|clean>", "detail": "<1 sentence>" },
    { "label": "Chroma Anomaly",        "status": "<detected|warning|clean>", "detail": "<1 sentence>" },
    { "label": "Splice / Boundary",     "status": "<detected|warning|clean>", "detail": "<1 sentence>" }
  ]
}

IMPORTANT: If the image looks fully authentic with no AI manipulation, return an empty regions array.
If parts are AI (e.g. AI background + real person), only mark the AI parts."""

class ClaudeVisionAnalyzer:
    """
    Phase 4: High-Fidelity Region Heatmap integration.
    Uses Anthropic's Claude 3.5 Sonnet to detect AI-manipulated regions and return polygons.
    """
    def __init__(self):
        self.api_key = os.environ.get("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=self.api_key) if HAS_ANTHROPIC and self.api_key else None

    async def load_model(self):
        if not HAS_ANTHROPIC:
            logger.warning("Anthropic package not installed. Claude Vision regions disabled.")
        elif not self.api_key:
            logger.warning("ANTHROPIC_API_KEY environment variable not found. Claude Vision regions disabled.")
        else:
            logger.info("ClaudeVisionAnalyzer ready.")

    def analyze(self, image_base64: str, mime_type: str = "image/jpeg") -> dict:
        """
        Calls Claude Vision to get the polygon regions.
        Returns a dictionary with 'regions', 'summary', and 'signals'.
        """
        # Default empty fallback
        fallback = {
            "ai_score": 0,
            "verdict": "AUTHENTIC",
            "summary": "Claude Vision API not configured or failed.",
            "regions": [],
            "signals": []
        }

        if not self.client:
            return fallback

        try:
            # Map common extensions if mime_type is missing/generic
            if not mime_type or mime_type == "application/octet-stream":
                mime_type = "image/jpeg"
                
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1500,
                temperature=0.0,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": mime_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": CLAUDE_PROMPT
                            }
                        ]
                    }
                ]
            )
            
            # Parse the JSON response
            text_response = response.content[0].text
            # Strip potential markdown blocks just in case
            if "```json" in text_response:
                text_response = text_response.split("```json")[1].split("```")[0]
            elif "```" in text_response:
                text_response = text_response.split("```")[1].split("```")[0]
                
            parsed = json.loads(text_response.strip())
            return {
                "ai_score": parsed.get("ai_score", 0),
                "verdict": parsed.get("verdict", "AUTHENTIC"),
                "summary": parsed.get("summary", ""),
                "regions": parsed.get("regions", []),
                "signals": parsed.get("signals", [])
            }

        except Exception as e:
            logger.error(f"Claude Vision API failed: {e}")
            return fallback

claude_analyzer = ClaudeVisionAnalyzer()
