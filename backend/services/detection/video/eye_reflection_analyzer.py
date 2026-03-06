import cv2
import numpy as np
from loguru import logger

class EyeReflectionAnalyzer:
    """
    Checks for geometric consistency of specular highlights (light reflections)
    in both eyes. Real humans always show the same light source reflected in both eyes.
    AI-generated faces often have mismatched, asymmetric, or absent reflections.
    """
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        logger.info("EyeReflectionAnalyzer initialized (specular highlight geometry check)")

    def _get_specular_point(self, eye_roi: np.ndarray) -> tuple | None:
        """Find the brightest point (specular highlight) in an eye ROI."""
        try:
            gray = cv2.cvtColor(eye_roi, cv2.COLOR_BGR2GRAY) if len(eye_roi.shape) == 3 else eye_roi
            if gray.size == 0:
                return None
            # Brightest pixel = specular highlight
            _, _, _, max_loc = cv2.minMaxLoc(gray)
            h, w = gray.shape
            # Normalize to 0-1 range
            return (max_loc[0] / w, max_loc[1] / h)
        except Exception:
            return None

    def _analyze_single_frame(self, frame: np.ndarray) -> float | None:
        """Returns asymmetry score for one frame, or None if no eyes found."""
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            if len(faces) == 0:
                return None

            fx, fy, fw, fh = faces[0]
            upper_face = frame[fy:fy + int(fh * 0.55), fx:fx + fw]
            upper_gray = cv2.cvtColor(upper_face, cv2.COLOR_BGR2GRAY)

            eyes = self.eye_cascade.detectMultiScale(
                upper_gray, scaleFactor=1.05, minNeighbors=5, minSize=(20, 20)
            )
            if len(eyes) < 2:
                return None

            # Sort eyes left to right
            eyes = sorted(eyes, key=lambda e: e[0])[:2]
            reflections = []
            for (ex, ey, ew, eh) in eyes:
                eye_roi = upper_face[ey:ey+eh, ex:ex+ew]
                pt = self._get_specular_point(eye_roi)
                if pt:
                    reflections.append(pt)

            if len(reflections) < 2:
                return None

            # Compute asymmetry: in real faces, reflection position should be roughly symmetric
            left_x, left_y = reflections[0]
            right_x, right_y = reflections[1]

            # X positions: left eye reflection should be mirror of right
            # Left eye: highlight should be on right side (toward camera center) — right_x should be < 0.5
            x_asymmetry = abs(left_x - (1.0 - right_x))  # ideal = 0
            y_asymmetry = abs(left_y - right_y)            # ideal = 0

            asymmetry = float(x_asymmetry * 0.6 + y_asymmetry * 0.4)
            return asymmetry

        except Exception:
            return None

    def analyze_frames(self, frames: list) -> dict:
        """Analyze eye reflection consistency across sampled frames."""
        if not frames:
            return {"score": 50.0, "detail": "No frames for eye reflection analysis"}

        # Sample 1/3 of frames for performance
        sample = frames[::max(1, len(frames)//6)]
        asymmetry_scores = []

        for frame in sample:
            score = self._analyze_single_frame(frame)
            if score is not None:
                asymmetry_scores.append(score)

        if not asymmetry_scores:
            return {"score": 30.0, "detail": "Eyes not detected — reflection analysis skipped"}

        mean_asym = float(np.mean(asymmetry_scores))
        max_asym = float(np.max(asymmetry_scores))

        # Scoring: >0.35 = very high asymmetry = strong AI indicator
        if mean_asym > 0.35:
            score = 85.0
            detail = f"High eye reflection asymmetry (avg={mean_asym:.2f}) — light source inconsistency detected across both eyes"
        elif mean_asym > 0.20:
            score = 50.0
            detail = f"Moderate eye reflection asymmetry (avg={mean_asym:.2f}) — possible scene inconsistency"
        else:
            score = 10.0
            detail = f"Eye reflections symmetric (avg={mean_asym:.2f}) — geometrically consistent light source"

        logger.info(f"EyeReflectionAnalyzer: score={score:.1f}, mean_asym={mean_asym:.2f}")
        return {
            "score": score,
            "detail": detail,
            "mean_asymmetry": round(mean_asym, 3),
            "max_asymmetry": round(max_asym, 3),
        }
