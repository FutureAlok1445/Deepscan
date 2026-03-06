import cv2
import numpy as np
import os
import tempfile
from loguru import logger

def calculate_probability(value, midpoint, steepness, reverse=False):
    """
    Sigmoid-based probability calculation.
    Higher value -> Higher score if not reverse.
    """
    score = 100 / (1 + np.exp(-steepness * (value - midpoint)))
    if reverse:
        return 100 - score
    return score

class ELAAnalyzer:
    """
    Error Level Analysis (ELA)
    Analyzes JPEG compression levels to find inconsistencies.
    Reasoning: Natural photos have a balanced distribution of high-frequency error.
    AI-generated patches or splicing leave 'flat' or 'extreme' error signatures.
    """
    def __init__(self, quality=90):
        self.quality = quality

    def analyze(self, image_path: str) -> dict:
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {"score": 50.0, "detail": "Unreadable", "reasoning": "Standard I/O failure."}

            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                temp_path = tmp.name
            cv2.imwrite(temp_path, img, [cv2.IMWRITE_JPEG_QUALITY, self.quality])
            compressed = cv2.imread(temp_path)
            os.remove(temp_path)

            if compressed is None:
                return {"score": 50.0, "detail": "Baseline failure", "reasoning": "Failed to generate ELA comparison image."}

            diff = cv2.absdiff(img, compressed)
            gray_diff = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            ela_std = np.std(gray_diff)

            # --- Logic ---
            # Normal range for real images: 4.0 - 12.0
            # AI/Diffusion: < 2.0 (Too smooth)
            # Spliced: > 20.0 (High edge contrast)
            
            if ela_std < 4.0:
                # Probability of being AI/Smooth increases as std approaches 0
                prob_ai = calculate_probability(ela_std, 2.0, -1.5) 
                score = prob_ai
                reasoning = f"The ELA standard deviation ({ela_std:.2f}) is significantly below the natural JPEG baseline (<4.0). This indicates an unnaturally uniform compression grid, a common fingerprint of Diffusion-based generative models."
            elif ela_std > 18.0:
                # Probability of being Spliced increases as std increases
                prob_spliced = calculate_probability(ela_std, 22.0, 0.5)
                score = prob_spliced
                reasoning = f"The ELA variance ({ela_std:.2f}) is abnormally high. This suggests sharp discontinuities in the compression levels, often caused by grafting/splicing high-frequency elements onto a different background."
            else:
                score = 15.0 # Baseline natural
                reasoning = f"ELA distribution ({ela_std:.2f}) falls within the expected range for authentic camera-captured content."

            return {
                "score": round(score, 1),
                "detail": f"StdDev: {ela_std:.2f}",
                "reasoning": reasoning,
                "ela_std": float(ela_std)
            }

        except Exception as e:
            logger.warning(f"ELAAnalyzer failed: {e}")
            return {"score": 50.0, "detail": "Error", "reasoning": str(e)}


class ImageNoiseAnalyzer:
    """
    High-Frequency Noise Variance (Sensor Pattern check)
    Reasoning: Silicon sensors (CMOS) produce specific high-frequency noise (PRNU).
    AI models lack a physical sensor and produce mathematically optimized smooth transitions.
    """
    def __init__(self):
        pass

    def analyze(self, image_path: str) -> dict:
        try:
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                return {"score": 50.0, "detail": "Unreadable", "reasoning": "Image could not be loaded for grayscale analysis."}

            blurred = cv2.medianBlur(img, 5)
            noise_residue = cv2.absdiff(img, blurred)
            noise_variance = np.var(noise_residue)

            # --- Logic ---
            # Real sensor noise variance: usually 15.0 to 100.0
            # AI images: usually < 8.0
            
            # Use a sigmoid centered at 12.0 to catch "Too Clean" images
            prob_synthetic = calculate_probability(noise_variance, 12.0, -0.4)
            
            if noise_variance < 10.0:
                score = prob_synthetic
                reasoning = f"Extremely low noise residue (Var={noise_variance:.2f}). Authentic CMOS sensors naturally produce random thermal and shot noise; the absence of this 'texture' strongly suggests a synthetic manifold."
            elif noise_variance > 180.0:
                score = 45.0
                reasoning = f"High noise variance ({noise_variance:.2f}). While high, this is more consistent with ISO noise or film grain in authentic captures rather than synthetic smoothing."
            else:
                score = 20.0
                reasoning = f"Detected natural high-frequency residue levels (Var={noise_variance:.2f}) consistent with physical camera sensors."

            return {
                "score": round(score, 1),
                "detail": f"Variance: {noise_variance:.2f}",
                "reasoning": reasoning,
                "variance": float(noise_variance)
            }

        except Exception as e:
            logger.warning(f"ImageNoiseAnalyzer failed: {e}")
            return {"score": 50.0, "detail": "Error", "reasoning": str(e)}
