import cv2
import numpy as np
from loguru import logger

class FaceMeshAnalyzer:
    """
    Tracks facial landmark stability across frames using sparse Lucas-Kanade optical flow.
    Detects 'chunk-boundary' warping common in Sora/Kling videos where the face
    model regenerates between latent chunks, causing sudden landmark jumps.
    """
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # LK params for tracking
        self.lk_params = dict(
            winSize=(15, 15),
            maxLevel=2,
            criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03)
        )
        logger.info("FaceMeshAnalyzer initialized (Lucas-Kanade landmark tracking)")

    def _get_face_features(self, gray_frame: np.ndarray, face_rect: tuple) -> np.ndarray | None:
        """Extract trackable feature points from face region using Shi-Tomasi."""
        try:
            fx, fy, fw, fh = face_rect
            face_roi = gray_frame[fy:fy+fh, fx:fx+fw]
            # Good Features To Track — equivalent to 68-point landmark priors
            pts = cv2.goodFeaturesToTrack(
                face_roi, maxCorners=40, qualityLevel=0.05,
                minDistance=7, blockSize=7
            )
            if pts is None:
                return None
            # Translate back to full-frame coords
            pts[:, :, 0] += fx
            pts[:, :, 1] += fy
            return pts.astype(np.float32)
        except Exception:
            return None

    def analyze_frames(self, frames: list) -> dict:
        """
        Track landmark stability across frame sequence.
        Returns instability score (0-100) and interpretation.
        """
        if len(frames) < 6:
            return {"score": 50.0, "detail": "Too few frames for mesh analysis"}

        gray_frames = []
        for f in frames:
            try:
                gray_frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
            except Exception:
                gray_frames.append(None)

        # Detect face in first frame
        face_rect = None
        for g in gray_frames[:5]:
            if g is None:
                continue
            faces = self.face_cascade.detectMultiScale(g, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
            if len(faces) > 0:
                face_rect = faces[0]
                break

        if face_rect is None:
            return {"score": 25.0, "detail": "No face detected for mesh tracking"}

        # Get initial feature points
        pts = self._get_face_features(gray_frames[0], face_rect)
        if pts is None or len(pts) < 5:
            return {"score": 25.0, "detail": "Insufficient facial features for tracking"}

        # Track across frames and measure velocity variance
        velocity_magnitudes = []
        sudden_jumps = 0
        JUMP_THRESHOLD = 8.0  # pixels per frame — AI chunk boundary artifact

        prev_gray = gray_frames[0]
        current_pts = pts.copy()

        for i in range(1, len(gray_frames)):
            if gray_frames[i] is None or prev_gray is None:
                continue
            try:
                next_pts, status, _ = cv2.calcOpticalFlowPyrLK(
                    prev_gray, gray_frames[i], current_pts, None, **self.lk_params
                )
                if next_pts is None or status is None:
                    continue

                good_new = next_pts[status == 1]
                good_old = current_pts[status == 1]

                if len(good_new) < 3:
                    continue

                # Velocity of each tracked point
                deltas = np.linalg.norm(good_new - good_old, axis=1)
                velocity_magnitudes.extend(deltas.tolist())

                # Sudden jump: most points move drastically in one frame (chunk boundary)
                if np.median(deltas) > JUMP_THRESHOLD:
                    sudden_jumps += 1

                current_pts = good_new.reshape(-1, 1, 2)
                prev_gray = gray_frames[i]
            except Exception:
                continue

        if not velocity_magnitudes:
            return {"score": 40.0, "detail": "Unable to track face landmarks"}

        velocity_std = float(np.std(velocity_magnitudes))
        velocity_mean = float(np.mean(velocity_magnitudes))
        
        # --- Scoring ---
        score = 0.0
        reasons = []

        if sudden_jumps >= 2:
            score += min(sudden_jumps * 20.0, 60.0)
            reasons.append(f"{sudden_jumps} sudden landmark jump(s) — indicates AI chunk boundary warping")

        # Very high velocity variance = jitter; very low = unnaturally smooth (AI)
        if velocity_std > 6.0:
            score += 35.0
            reasons.append(f"High landmark jitter (std={velocity_std:.1f}px) — temporal incoherence detected")
        elif velocity_std < 0.5 and velocity_mean > 0.5:
            score += 40.0
            reasons.append(f"Suspiciously smooth motion (std={velocity_std:.2f}px) — may indicate AI generation")

        score = float(np.clip(score, 0.0, 100.0))
        detail = "; ".join(reasons) if reasons else f"Face mesh stable (jitter std={velocity_std:.2f}px, jumps={sudden_jumps})"

        logger.info(f"FaceMeshAnalyzer: score={score:.1f}, jitter_std={velocity_std:.2f}, jumps={sudden_jumps}")
        return {
            "score": score,
            "detail": detail,
            "jitter_std": round(velocity_std, 2),
            "sudden_jumps": sudden_jumps,
        }
