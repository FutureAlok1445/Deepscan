import cv2
import numpy as np
from loguru import logger

class BlinkAnalyzer:
    """
    Detects unnatural eye blinking patterns using Eye Aspect Ratio (EAR).
    Real human blinks: ~0.3s duration, 15-20/min frequency, slightly irregular timing.
    AI-generated: no blinks, single-frame blinks, or robotically uniform blinks.
    """
    EAR_THRESHOLD = 0.22    # below this = eye closing
    MIN_BLINK_FRAMES = 2    # minimum consecutive frames for valid blink
    MAX_BLINK_FRAMES = 8    # more than this = physically impossible fast blink logged differently

    def __init__(self):
        self.eye_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        logger.info("BlinkAnalyzer initialized (EAR-based blink detection)")

    def _get_eye_aspect_ratio(self, eye_region: np.ndarray) -> float:
        """Compute EAR from an eye ROI using brightness profile."""
        try:
            if eye_region is None or eye_region.size == 0:
                return 0.3  # neutral
            gray = cv2.cvtColor(eye_region, cv2.COLOR_BGR2GRAY) if len(eye_region.shape) == 3 else eye_region
            h, w = gray.shape
            if h == 0 or w == 0:
                return 0.3
            # Vertical profile — ratio of open height to total height
            col_means = np.mean(gray, axis=1)
            # EAR proxy: dark region (low brightness) in center = open eye
            center_brightness = np.mean(col_means[h//4: 3*h//4])
            edge_brightness = np.mean(np.concatenate([col_means[:h//4], col_means[3*h//4:]]))
            
            if edge_brightness == 0:
                return 0.3
            # Low center/edge ratio = open eye; high ratio = closed/blinking
            ratio = center_brightness / (edge_brightness + 1e-6)
            ear = 1.0 - min(ratio, 1.0)  # invert: high = open
            return float(ear)
        except Exception:
            return 0.3

    def analyze_frames(self, frames: list, fps: float = 30.0) -> dict:
        """
        Analyze a sequence of frames for blink patterns.
        Returns a score (0-100) and details.
        """
        if len(frames) < 10:
            return {"score": 50.0, "detail": "Too few frames for blink analysis", "blinks_detected": 0}

        ear_series = []
        face_found = False

        for frame in frames:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Detect faces
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
                if len(faces) == 0:
                    ear_series.append(0.3)  # neutral if no face
                    continue
                
                face_found = True
                fx, fy, fw, fh = faces[0]
                # Look for eyes in upper-half of face
                upper_face = frame[fy:fy + fh//2, fx:fx + fw]
                eyes = self.eye_cascade.detectMultiScale(
                    cv2.cvtColor(upper_face, cv2.COLOR_BGR2GRAY),
                    scaleFactor=1.1, minNeighbors=5, minSize=(20, 20)
                )
                
                if len(eyes) >= 2:
                    ears = [self._get_eye_aspect_ratio(upper_face[ey:ey+eh, ex:ex+ew]) for (ex, ey, ew, eh) in eyes[:2]]
                    ear_series.append(np.mean(ears))
                elif len(eyes) == 1:
                    ex, ey, ew, eh = eyes[0]
                    ear_series.append(self._get_eye_aspect_ratio(upper_face[ey:ey+eh, ex:ex+ew]))
                else:
                    ear_series.append(0.3)
            except Exception:
                ear_series.append(0.3)

        if not face_found:
            return {"score": 30.0, "detail": "No face detected — cannot perform blink analysis", "blinks_detected": 0}

        # --- Blink detection from EAR series ---
        blink_durations = []
        in_blink = False
        blink_len = 0

        for ear in ear_series:
            if ear < self.EAR_THRESHOLD:
                if not in_blink:
                    in_blink = True
                    blink_len = 1
                else:
                    blink_len += 1
            else:
                if in_blink:
                    if self.MIN_BLINK_FRAMES <= blink_len <= self.MAX_BLINK_FRAMES:
                        blink_durations.append(blink_len)
                    in_blink = False
                    blink_len = 0

        n_blinks = len(blink_durations)
        total_seconds = len(frames) / fps
        blink_rate = (n_blinks / total_seconds) * 60 if total_seconds > 0 else 0

        # --- Scoring ---
        score = 0.0
        reasons = []

        # No blinks in > 5 seconds
        if n_blinks == 0 and total_seconds > 5:
            score += 70.0
            reasons.append("No blinks detected — strongly suggests AI generation")
        elif blink_rate < 3 and total_seconds > 8:
            score += 40.0
            reasons.append(f"Abnormally low blink rate ({blink_rate:.1f}/min; human avg: 15-20/min)")
        elif blink_rate > 40:
            score += 35.0
            reasons.append(f"Unusually high blink frequency ({blink_rate:.1f}/min)")

        # Single-frame blinks (AI glitch)
        single_frame_blinks = sum(1 for d in blink_durations if d <= 1)
        if single_frame_blinks > 0:
            score += min(single_frame_blinks * 25.0, 60.0)
            reasons.append(f"{single_frame_blinks} single-frame blink(s) detected — physically impossible at {fps:.0f}fps")

        # Robotic regularity (all blinks same duration)
        if n_blinks >= 3 and np.std(blink_durations) < 0.5:
            score += 30.0
            reasons.append("All blinks identical duration — robotic regularity detected")

        score = float(np.clip(score, 0.0, 100.0))
        detail = "; ".join(reasons) if reasons else f"Blink pattern normal ({n_blinks} blinks, {blink_rate:.1f}/min)"

        logger.info(f"BlinkAnalyzer: score={score:.1f}, blinks={n_blinks}, rate={blink_rate:.1f}/min")
        return {
            "score": score,
            "detail": detail,
            "blinks_detected": n_blinks,
            "blink_rate_per_min": round(blink_rate, 1),
        }
