import os
import asyncio
from loguru import logger
from backend.utils.hf_api import query_huggingface

class AudioDetector:
    def __init__(self):
        # Specially trained model for audio spoofing/deepfake detection
        self.model_id = "umm-maybe/AI-Voice-Detector" # or "MelodyMachine/Deepfake-Audio-Detection-V2"
        logger.info(f"AudioDetector initialized with HF model: {self.model_id}")

    async def analyze(self, file_path: str) -> float:
        """
        Detects if audio is a voice clone or AI-generated.
        Returns a score from 0 to 100 (where 100 is definitely fake).
        """
        try:
            result = await query_huggingface(self.model_id, file_path=file_path)
            
            if "error" in result:
                logger.error(f"AudioDetector API error: {result['error']}")
                return 50.0

            # Expected format: [{"label": "fake", "score": 0.9}, {"label": "real", "score": 0.1}]
            fake_score = 0.0
            if isinstance(result, list):
                for item in result:
                    label = str(item.get("label", "")).lower()
                    if label in ["fake", "spoof", "ai", "synthetic", "label_1"]:
                        fake_score = item.get("score", 0.0)
                        break
                    if label in ["real", "bonafide", "human", "label_0"]:
                        fake_score = 1.0 - item.get("score", 1.0)
                        break
            
            return round(fake_score * 100, 2)

        except Exception as e:
            logger.error(f"AudioDetector.analyze failed: {e}")
            return 50.0