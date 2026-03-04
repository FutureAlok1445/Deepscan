from loguru import logger

try:
    import numpy as np
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2/numpy not installed — FFTAnalyzer will return heuristic scores")


class FFTAnalyzer:
    def analyze(self, image_path: str) -> dict:
        if not HAS_CV2:
            return {"fft_score": 50.0}
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return {"fft_score": 50.0}
            fft = np.fft.fftshift(np.fft.fft2(img))
            magnitude = np.abs(fft) + 1e-10  # avoid log(0) producing -inf/NaN
            return {"fft_score": float(np.mean(20 * np.log(magnitude)) % 100.0)}
        except Exception:
            return {"fft_score": 50.0}