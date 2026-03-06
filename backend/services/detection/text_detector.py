from loguru import logger
from backend.utils.hf_api import query_huggingface

class TextDetector:
    def __init__(self):
        # State-of-the-art AI text detector
        self.model_id = "desklib/ai-text-detector-v1.01"
        logger.info(f"TextDetector initialized with HF model: {self.model_id}")

    async def analyze(self, text: str) -> float:
        """
        Analyzes if text is AI-generated (e.g., GPT, Claude).
        Returns a score from 0 to 100 (where 100 is definitely AI-generated).
        """
        if not text.strip() or len(text.split()) < 5:
            return 0.0

        try:
            result = await query_huggingface(self.model_id, payload={"inputs": text})
            
            if "error" in result:
                logger.error(f"TextDetector API error: {result['error']}")
                return 40.0  # Heuristic fallback for short/ambiguous text

            # Model typically returns: [[{"label": "AI", "score": 0.9}, {"label": "Human", "score": 0.1}]]
            ai_score = 0.0
            if isinstance(result, list) and len(result) > 0:
                inner = result[0]
                for item in inner:
                    label = str(item.get("label", "")).lower()
                    if "ai" in label or "label_1" in label or "fake" in label:
                        ai_score = item.get("score", 0.0)
                        break
                    if "human" in label or "label_0" in label:
                        ai_score = 1.0 - item.get("score", 1.0)
                        break
            
            return round(ai_score * 100, 2)

        except Exception as e:
            logger.error(f"TextDetector.analyze failed: {e}")
            return 50.0