import os
import asyncio
from loguru import logger
from backend.utils.hf_api import query_huggingface

class ImageDetector:
    def __init__(self):
        # We now use the Hugging Face Inference API instead of local model loading
        # to ensure high accuracy without massive local GPU requirements.
        self.model_id = "prithivMLmods/Deep-Fake-Detector-v2-Model"
        logger.info(f"ImageDetector initialized with HF model: {self.model_id}")

    def predict(self, image_path: str) -> float:
        """
        Synchronous wrapper for predict_async to maintain compatibility 
        with existing orchestrator signature if needed, though orchestrator 
        is async-capable.
        """
        return asyncio.run(self.predict_async(image_path))

    async def predict_async(self, image_path: str) -> float:
        """
        Detects if an image is a deepfake using a Vision Transformer (ViT).
        Returns a score from 0 to 100 (where 100 is definitely fake).
        """
        try:
            result = await query_huggingface(self.model_id, file_path=image_path)
            
            if "error" in result:
                logger.error(f"ImageDetector API error: {result['error']}")
                return 50.0  # Fallback to neutral score

            # Expected format: [{"label": "Real", "score": 0.9}, {"label": "Fake", "score": 0.1}]
            # or simply a list of scores.
            fake_score = 0.0
            if isinstance(result, list):
                for item in result:
                    label = str(item.get("label", "")).lower()
                    if label in ["fake", "deepfake", "label_1", "synthetic"]:
                        fake_score = item.get("score", 0.0)
                        break
                    # If model returns "Realism" / "Deepfake"
                    if label == "deepfake":
                        fake_score = item.get("score", 0.0)
                        break
                
                # If we only found a high "Real" score, the fake score is 1 - real
                if fake_score == 0.0:
                    for item in result:
                        label = str(item.get("label", "")).lower()
                        if label in ["real", "authentic", "label_0", "realism"]:
                            fake_score = 1.0 - item.get("score", 1.0)
                            break
            
            return round(fake_score * 100, 2)

        except Exception as e:
            logger.error(f"ImageDetector.predict_async failed: {e}")
            return 50.0