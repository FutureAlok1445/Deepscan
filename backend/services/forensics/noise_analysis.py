from loguru import logger

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2 not installed — NoiseAnalyzer will return heuristic scores")


class NoiseAnalyzer:
    def evaluate(self, image_path: str) -> float:
        if not HAS_CV2:
            return 50.0
        try:
            img = cv2.imread(image_path)
            if img is None:
                return 50.0
            return float(max(0.0, min(100.0, 100.0 - (cv2.Laplacian(img, cv2.CV_64F).var() / 10.0))))
        except Exception:
            return 50.0