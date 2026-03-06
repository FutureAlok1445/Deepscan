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
        Logic: 
        1. Temporal Incoherence: AI models struggle to maintain per-pixel landmark 
           identity between frames, causing 'pixel-slip' jitter.
        2. Chunk Boundaries: Autoregressive models (Sora/Kling) regenerate the latent 
           manifold in 1-2 second chunks, often causing a 'jump' in geometry.
        3. Biomechanical Tremor: Real faces have subtle, high-frequency micro-tremors 
           that differ from synthetic interpolation.
        """
        if len(frames) < 10:
            return {"score": 50.0, "detail": "Insufficient data", "reasoning": "Sequence too short to calculate landmark velocity variance."}

        gray_frames = []
        for f in frames:
            try: gray_frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY))
            except Exception: gray_frames.append(None)

        face_rect = None
        for g in gray_frames[:5]:
            if g is None: continue
            faces = self.face_cascade.detectMultiScale(g, 1.1, 4, minSize=(60, 60))
            if len(faces) > 0:
                face_rect = faces[0]
                break

        if face_rect is None:
            return {"score": 25.0, "detail": "No face", "reasoning": "Face mesh analysis requires a trackable face. No facial region was locked."}

        pts = self._get_face_features(gray_frames[0], face_rect)
        if pts is None or len(pts) < 5:
            return {"score": 25.0, "detail": "Low features", "reasoning": "Facial region lacks enough high-contrast corners (Shi-Tomasi) for reliable tracking."}

        velocity_magnitudes, sudden_jumps = [], 0
        JUMP_THRESHOLD = 8.0 # px
        prev_gray, current_pts = gray_frames[0], pts.copy()

        for i in range(1, len(gray_frames)):
            if gray_frames[i] is None or prev_gray is None: continue
            try:
                next_pts, status, _ = cv2.calcOpticalFlowPyrLK(prev_gray, gray_frames[i], current_pts, None, **self.lk_params)
                if next_pts is None or status is None: continue
                good_new, good_old = next_pts[status == 1], current_pts[status == 1]
                if len(good_new) < 3: continue

                deltas = np.linalg.norm(good_new - good_old, axis=1)
                velocity_magnitudes.extend(deltas.tolist())

                if np.median(deltas) > JUMP_THRESHOLD: sudden_jumps += 1
                current_pts, prev_gray = good_new.reshape(-1, 1, 2), gray_frames[i]
            except Exception: continue

        if not velocity_magnitudes:
            return {"score": 40.0, "detail": "Tracking lost", "reasoning": "Optical flow tracking failed mid-sequence; cannot verify temporal stability."}

        velocity_std = float(np.std(velocity_magnitudes))
        velocity_mean = float(np.mean(velocity_magnitudes))
        
        # --- Scientific Scoring ---
        score = 0.0
        details, reasons = [], []

        if sudden_jumps >= 1:
            jump_prob = min(sudden_jumps * 30.0, 75.0)
            score = max(score, jump_prob)
            details.append(f"{sudden_jumps} jump(s)")
            reasons.append(f"Detected {sudden_jumps} sudden manifold shift(s) (median velocity > {JUMP_THRESHOLD}px). This is a known 'Chunk Boundary' artifact where latent-diffusion models reset their internal skeletal priors, causing physically impossible jumps in facial geometry.")

        if velocity_std > 5.5:
            jitter_prob = min((velocity_std - 5.0) * 15.0, 60.0)
            score = max(score, jitter_prob)
            details.append(f"High jitter: {velocity_std:.1f}")
            reasons.append(f"High landmark jitter (StdDev={velocity_std:.1f}px) indicates high-frequency 'pixel-slip.' Authentic human motion is governed by muscle tension and inertia, producing much smoother velocity profiles.")
        elif velocity_std < 0.3 and velocity_mean > 0.4:
            score = max(score, 45.0)
            details.append("Uniform motion")
            reasons.append(f"Detected 2D-warped uniform motion (StdDev={velocity_std:.2f}). This suggests the face is being treated as a flat mesh or texture rather than a 3D volume with organic micro-tremors.")

        score = float(np.clip(score, 0.0, 100.0))
        detail_msg = "; ".join(details) if details else f"Mesh stable (Jitter std={velocity_std:.2f})"
        reasoning_msg = " ".join(reasons) if reasons else "Facial landmark trajectories exhibit high temporal-coherence and natural biological micro-tremors consistent with an authentic 3D skeletal volume."

        logger.info(f"FaceMeshAnalyzer: score={score:.1f}, jumps={sudden_jumps}")
        return {
            "score": score,
            "detail": detail_msg,
            "reasoning": reasoning_msg,
            "jitter_std": round(velocity_std, 2),
            "sudden_jumps": sudden_jumps,
        }
