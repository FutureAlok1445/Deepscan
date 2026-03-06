from loguru import logger

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    # Provide a dummy np so type hints (np.ndarray) don't crash at class definition
    import types
    np = types.SimpleNamespace(ndarray=object, array=lambda *a, **k: [], mean=lambda *a: 0, std=lambda *a: 0, linspace=lambda *a, **k: [], any=lambda *a: False, abs=lambda *a: [], argmax=lambda *a: 0)
    np.fft = types.SimpleNamespace(rfft=lambda *a: [], rfftfreq=lambda *a, **k: [])
    logger.warning("cv2/numpy not installed — RPPGDetector will return heuristic scores")

from backend.services.physiological.face_roi_extractor import FaceROIExtractor
from backend.services.physiological.signal_processor import apply_filter
from backend.services.physiological.heartbeat_validator import HeartbeatValidator


class RPPGDetector:
    """Remote Photoplethysmography (rPPG) detector.

    Extracts subtle skin color variations from video frames to estimate
    heart rate. Deepfakes lack genuine micro-circulation signals, so
    absent or implausible HR is a strong manipulation indicator.
    """

    def __init__(self):
        self.face_extractor = FaceROIExtractor()
        self.validator = HeartbeatValidator()
        self.fps = 30.0  # assumed capture frame rate

    def _extract_green_channel_signal(self, video_path: str, max_frames: int = 300) -> tuple:
        """Extract mean green channel intensity from face ROI per frame."""
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return np.array([]), 0

        fps = cap.get(cv2.CAP_PROP_FPS) or self.fps
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        sample_count = min(total_frames, max_frames)
        indices = np.linspace(0, total_frames - 1, sample_count, dtype=int)

        green_signal = []
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )

        for idx in indices:
            cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
            ret, frame = cap.read()
            if not ret:
                continue

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)

            if len(faces) > 0:
                # Use the largest face
                x, y, w, h = max(faces, key=lambda f: f[2] * f[3])
                # Focus on forehead region (top 30% of face) — best for rPPG
                forehead = frame[y : y + int(h * 0.3), x : x + w]
                if forehead.size > 0:
                    green_signal.append(float(np.mean(forehead[:, :, 1])))  # Green channel
                else:
                    green_signal.append(0.0)
            else:
                green_signal.append(0.0)

        cap.release()
        return np.array(green_signal), fps

    def _estimate_heart_rate(self, signal: np.ndarray, fps: float) -> float:
        """Estimate BPM from the filtered green channel signal using FFT."""
        if len(signal) < 30:
            return 0.0

        # Remove DC component
        signal = signal - np.mean(signal)

        # Apply bandpass filter (0.7–4.0 Hz = 42–240 BPM)
        try:
            filtered = apply_filter(signal, fs=fps, lowcut=0.7, highcut=4.0)
        except Exception:
            filtered = signal

        # FFT to find dominant frequency
        n = len(filtered)
        fft_vals = np.abs(np.fft.rfft(filtered))
        freqs = np.fft.rfftfreq(n, d=1.0 / fps)

        # Only look at physiological range (0.7–3.5 Hz = 42–210 BPM)
        valid = (freqs >= 0.7) & (freqs <= 3.5)
        if not np.any(valid):
            return 0.0

        fft_valid = fft_vals[valid]
        freq_valid = freqs[valid]

        dominant_freq = freq_valid[np.argmax(fft_valid)]
        bpm = dominant_freq * 60.0

        return round(bpm, 1)

    def _compute_signal_quality(self, signal: np.ndarray) -> float:
        """Compute confidence score (0-1) based on signal quality."""
        if len(signal) < 10:
            return 0.0

        # Check for zero/missing values
        nonzero = signal[signal > 0]
        coverage = len(nonzero) / len(signal)

        if coverage < 0.3:
            return 0.0

        # Signal-to-noise ratio proxy
        std = np.std(nonzero)
        mean = np.mean(nonzero)
        if mean == 0:
            return 0.0

        cv = std / mean  # coefficient of variation
        # Good rPPG signals have low CV (0.01-0.05)
        if cv < 0.01:
            quality = 0.3  # too flat — likely no real signal
        elif cv < 0.05:
            quality = 0.9  # ideal range
        elif cv < 0.10:
            quality = 0.7
        else:
            quality = 0.4  # too noisy

        return round(quality * coverage, 2)

    def process_video(self, video_path: str) -> dict:
        """Run full rPPG analysis on a video file.

        Returns:
            dict with heart_rate, confidence, deepfake_prob, signal
        """
        logger.info(f"rPPG analysis starting: {video_path}")

        if not HAS_CV2:
            return {
                "heart_rate": 0,
                "confidence": 0.0,
                "deepfake_prob": 50.0,
                "signal": [],
                "analysis_note": "cv2 not available — rPPG analysis skipped",
            }

        try:
            signal, fps = self._extract_green_channel_signal(video_path)

            if len(signal) < 30:
                logger.warning("Insufficient frames for rPPG analysis")
                return {
                    "heart_rate": 0,
                    "confidence": 0.0,
                    "deepfake_prob": 75.0,
                    "signal": [],
                    "analysis_note": "Insufficient face frames detected",
                }

            heart_rate = self._estimate_heart_rate(signal, fps)
            confidence = self._compute_signal_quality(signal)

            # Validate physiological plausibility
            is_valid, reason = self.validator.validate(signal, heart_rate)

            # Compute deepfake probability
            if confidence < 0.2:
                # Very low signal quality — likely deepfake (no real blood flow)
                deepfake_prob = 85.0 + (1 - confidence) * 15
            elif not is_valid:
                # Implausible HR — suspicious
                deepfake_prob = 70.0
            elif heart_rate == 0:
                # No detectable HR
                deepfake_prob = 80.0
            else:
                # Valid HR detected — scale inversely with confidence
                deepfake_prob = max(5.0, 50.0 * (1 - confidence))

            deepfake_prob = round(min(100.0, max(0.0, deepfake_prob)), 1)

            # Downsample signal for frontend visualization (max 120 points)
            vis_signal = signal.tolist()
            if len(vis_signal) > 120:
                step = len(vis_signal) / 120
                vis_signal = [vis_signal[int(i * step)] for i in range(120)]

            logger.info(
                f"rPPG result: HR={heart_rate} BPM, "
                f"confidence={confidence:.2f}, "
                f"deepfake_prob={deepfake_prob:.1f}%"
            )

            return {
                "heart_rate": heart_rate,
                "confidence": confidence,
                "deepfake_prob": deepfake_prob,
                "signal": vis_signal,
                "is_valid": is_valid,
                "analysis_note": reason,
            }

        except Exception as e:
            logger.error(f"rPPG analysis failed: {e}")
            return {
                "heart_rate": 0,
                "confidence": 0.0,
                "deepfake_prob": 50.0,
                "signal": [],
                "analysis_note": f"Error: {str(e)}",
            }