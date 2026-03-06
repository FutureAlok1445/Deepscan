from loguru import logger

try:
    from transformers import pipeline as hf_pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("transformers not installed — TextDetector will return heuristic scores")


class TextDetector:
    def __init__(self):
        self.classifier = None
        if HAS_TRANSFORMERS:
            try:
                self.classifier = hf_pipeline("text-classification", model="distilbert-base-uncased-finetuned-sst-2-english", top_k=None)
            except Exception:
                self.classifier = None

    def analyze(self, text: str) -> float:
        if not text.strip():
            return 0.0
        if self.classifier:
            try:
                for res in self.classifier(text)[0]:
                    if res['label'] == 'NEGATIVE':
                        return float(res['score'] * 100.0)
                return 50.0
            except Exception:
                pass
        # Heuristic fallback
        suspicious = ["fake", "manipulated", "generated", "synthetic", "deepfake", "ai-generated"]
        words = text.lower().split()
        hits = sum(1 for w in words if any(s in w for s in suspicious))
        return min(float(hits * 15.0 + 20.0), 85.0) if hits else 10.0