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
        Using physiological constants for human blinking:
        - Rate: 12-20 blinks per minute (at rest)
        - Duration: 100ms - 400ms (3 to 12 frames at 30fps)
        - Variability: Inter-blink intervals are stochastic (non-uniform).
        """
        if len(frames) < 10:
            return {"score": 50.0, "detail": "Insufficient data", "reasoning": "Sequence too short to establish a baseline blink rate."}

        ear_series = []
        face_found = False

        for frame in frames:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(60, 60))
                if len(faces) == 0:
                    ear_series.append(0.3)
                    continue
                
                face_found = True
                fx, fy, fw, fh = faces[0]
                upper_face = frame[fy:fy + fh//2, fx:fx + fw]
                eyes = self.eye_cascade.detectMultiScale(cv2.cvtColor(upper_face, cv2.COLOR_BGR2GRAY), 1.1, 5, minSize=(20, 20))
                
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
            return {"score": 30.0, "detail": "No face", "reasoning": "Facial region not isolated; EAR metrics cannot be computed."}

        # --- Blink detection from EAR series ---
        blink_durations = []
        in_blink = False
        blink_len = 0

        for ear in ear_series:
            if ear < self.EAR_THRESHOLD:
                if not in_blink:
                    in_blink, blink_len = True, 1
                else:
                    blink_len += 1
            else:
                if in_blink:
                    if 1 <= blink_len <= 15: # Broad range for raw detection
                        blink_durations.append(blink_len)
                    in_blink, blink_len = False, 0

        n_blinks = len(blink_durations)
        total_seconds = len(frames) / fps
        blink_rate = (n_blinks / total_seconds) * 60 if total_seconds > 0 else 0

        # --- Scientific Scoring Logic ---
        score = 0.0
        details = []
        reasoning_list = []

        # 1. Rate Check (Human baseline: 10-25/min)
        if n_blinks == 0 and total_seconds > 6:
            score += 75.0
            details.append("Zero blinks")
            reasoning_list.append(f"No blinks detected over {total_seconds:.1f}s. A physiological 'blinkless' state is a hallmark of older GAN generators and shallow deepfakes.")
        elif blink_rate < 5:
            score += 45.0
            details.append(f"Low rate: {blink_rate:.1f}/m")
            reasoning_list.append("Sub-optimal blink frequency detected (Hypometropic pattern).")

        # 2. Duration Check: Single-frame blinks (Glitches)
        single_frame_blinks = sum(1 for d in blink_durations if d <= 1)
        if single_frame_blinks > 0 and fps >= 24:
            penalty = min(single_frame_blinks * 20.0, 50.0)
            score += penalty
            details.append(f"{single_frame_blinks} glitches")
            reasoning_list.append(f"Detected {single_frame_blinks} 'one-frame' blinks. At {fps:.0f}fps, a human blink physically requires ~100-300ms (3-9 frames). Near-instantaneous blinks are mathematical artifacts of frame-by-frame synthesis.")

        # 3. Regularity Check: Robotic uniformity
        if n_blinks >= 3:
            duration_std = np.std(blink_durations)
            if duration_std < 0.4: # All blinks nearly identical length
                score += 35.0
                details.append("Uniform rhythm")
                reasoning_list.append("Blink durations exhibit 'Robotic Regularity' (Standard Deviation < 0.4). Authentic human behavior is stochastic; perfectly timed blinks suggest parametric control.")

        score = float(np.clip(score, 0.0, 100.0))
        detail_msg = "; ".join(details) if details else f"Normal ({n_blinks} blinks, {blink_rate:.1f}/min)"
        reasoning_msg = " ".join(reasoning_list) if reasoning_list else "Blink patterns show natural frequency, duration, and temporal variance consistent with authentic human physiology."

        logger.info(f"BlinkAnalyzer: score={score:.1f}, rate={blink_rate:.1f}/min")
        return {
            "score": score,
            "detail": detail_msg,
            "reasoning": reasoning_msg,
            "blinks_detected": n_blinks,
            "blink_rate_per_min": round(blink_rate, 1),
        }
