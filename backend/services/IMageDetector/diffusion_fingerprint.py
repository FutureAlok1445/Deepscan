import os
from loguru import logger
from PIL import Image

try:
    from transformers import pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

class DiffusionFingerprintAnalyzer:
    """
    Phase 5: Advanced Diffusion Fingerprint Detection.
    Uses Hugging Face 'umm-maybe/AI-image-detector' to detect mathematical noise artifacts
    inherent in Stable Diffusion, Midjourney, and DALL-E generation processes.
    """
    def __init__(self):
        self.detector = None
        self.model_name = "umm-maybe/AI-image-detector"
        self.is_ready = False

    async def load_model(self):
        if not HAS_TRANSFORMERS:
            logger.warning("transformers not installed - Diffusion Fingerprint layer disabled.")
            return

        try:
            # Load the pre-trained vision transformer for AI detection
            logger.info(f"Loading Diffusion Fingerprint Model: {self.model_name}")
            self.detector = pipeline(
                "image-classification", 
                model=self.model_name,
                use_safetensors=False
            )
            self.is_ready = True
            logger.info("Diffusion Fingerprint layer loaded successfully.")
        except Exception as e:
            logger.error(f"Failed to load Diffusion Fingerprint model: {e}")

    def analyze(self, image_path: str) -> dict:
        """
        Analyzes the image for diffusion noise fingerprints.
        Returns a dictionary with the raw score and details.
        """
        fallback_result = {
            "score_diffusion": 0.0,
            "details": ["Diffusion fingerprint detector not loaded or failed."]
        }

        if not self.is_ready or not self.detector:
            return fallback_result

        try:
            img = Image.open(image_path).convert('RGB')
            # The pipeline returns a list of dicts like: [{'label': 'artificial', 'score': 0.9}, {'label': 'human', 'score': 0.1}]
            # Note: The exact labels vary by model, but we look for 'artificial', 'fake', or similar.
            results = self.detector(img)
            
            ai_probability = 0.0
            for res in results:
                label = res.get('label', '').lower()
                if 'artificial' in label or 'fake' in label or 'ai' in label:
                    ai_probability = res.get('score', 0.0) * 100
                    break
            
            # If the model strictly returns a single max confidence score and doesn't explicitly label 'artificial':
            if ai_probability == 0.0 and len(results) > 0:
                # Fallback: if label isn't obviously 'fake', handle according to model spec 
                # (umm-maybe returns 'artificial' / 'human')
                pass

            details = []
            if ai_probability > 75.0:
                 details.append(f"High-confidence diffusion noise fingerprint detected ({ai_probability:.1f}%).")
            elif ai_probability > 40.0:
                 details.append(f"Suspicious noise patterns found, possible diffusion artifacts ({ai_probability:.1f}%).")
            else:
                 details.append(f"Natural sensor noise detected; no diffusion artifacts found ({ai_probability:.1f}% AI probability).")

            return {
                "score_diffusion": round(ai_probability, 1),
                "details": details
            }

        except Exception as e:
            logger.error(f"Diffusion Fingerprint analysis failed: {e}")
            return fallback_result

diffusion_analyzer = DiffusionFingerprintAnalyzer()
