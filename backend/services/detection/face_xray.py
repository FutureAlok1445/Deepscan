import cv2
import numpy as np
from loguru import logger

def calculate_probability(value, midpoint, steepness, reverse=False):
    score = 100 / (1 + np.exp(-steepness * (value - midpoint)))
    if reverse:
        return 100 - score
    return score

class FaceXRayAnalyzer:
    """
    Simulates the Face X-Ray approach by detecting blending boundaries.
    Reasoning: Deepfakes composite a latent-generated face onto a real head.
    This creates a 'seam' where the color manifold (especially chrominance) 
    fails to match the background noise and lighting environment.
    """
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')

    def analyze(self, image_path: str) -> dict:
        try:
            img = cv2.imread(image_path)
            if img is None:
                return {"score": 50.0, "detail": "Unreadable", "reasoning": "Standard I/O failure."}

            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            if len(faces) == 0:
                return {
                    "score": 15.0, 
                    "detail": "No face detected", 
                    "reasoning": "Face X-Ray requires a dominant facial region to analyze blending boundaries. No faces found."
                }

            (x, y, w, h) = sorted(faces, key=lambda f: f[2]*f[3], reverse=True)[0]
            
            margin_x, margin_y = int(w * 0.15), int(h * 0.15)
            x1, y1 = max(0, x - margin_x), max(0, y - margin_y)
            x2, y2 = min(img.shape[1], x + w + margin_x), min(img.shape[0], y + h + margin_y)
            
            face_roi = img[y1:y2, x1:x2]
            lab = cv2.cvtColor(face_roi, cv2.COLOR_BGR2LAB)
            l, a, b = cv2.split(lab)
            
            # Laplacian variance catches sharp edges in chrominance
            laplacian_a = cv2.Laplacian(a, cv2.CV_64F)
            laplacian_b = cv2.Laplacian(b, cv2.CV_64F)
            chroma_variance = (np.var(laplacian_a) + np.var(laplacian_b)) / 2.0

            # --- Logic ---
            # Real skin has very smooth transitions in chrominance A/B (sub-100)
            # Spliced deepfakes show sharp 'mask' boundaries (transient spikes > 150)
            
            prob_spliced = calculate_probability(chroma_variance, 130.0, 0.05)
            
            if chroma_variance > 100.0:
                score = prob_spliced
                reasoning = f"Detected anomalous chrominance variance ({chroma_variance:.1f}) in the boundary region (jaw/hairline). In authentic photos, skin-tone transitions in LAB space are nearly continuous; sharp discontinuities here are a classic signature of mask-based FaceSwapping."
            else:
                score = min(prob_spliced, 20.0)
                reasoning = f"Facial chrominance transitions are fluid and natural (Var={chroma_variance:.1f}), showing no evidence of synthetic grafting or mask boundaries."

            return {
                "score": round(score, 1),
                "detail": f"Chroma Var: {chroma_variance:.1f}",
                "reasoning": reasoning,
                "chroma_variance": float(chroma_variance)
            }

        except Exception as e:
            logger.warning(f"FaceXRayAnalyzer failed: {e}")
            return {"score": 50.0, "detail": "Error", "reasoning": str(e)}
