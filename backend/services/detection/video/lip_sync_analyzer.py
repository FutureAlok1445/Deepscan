import cv2
import numpy as np
import subprocess
import tempfile
import os
from loguru import logger

class LipSyncAnalyzer:
    """
    Cross-correlates mouth aperture (visual signal) against audio energy (acoustic signal).
    A deepfake renders video and audio independently — resulting in a temporal desync
    or a phoneme-viseme mismatch (e.g., 'B' sound without lips closing).
    """
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        logger.info("LipSyncAnalyzer initialized (AV cross-correlation)")

    def _extract_audio_energy(self, video_path: str, n_windows: int) -> np.ndarray | None:
        """Extract per-window RMS audio energy using FFmpeg."""
        try:
            # Write audio to temp WAV using FFmpeg
            tmp_wav = tempfile.mktemp(suffix=".wav")
            result = subprocess.run(
                ["ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
                 "-ar", "16000", "-ac", "1", tmp_wav, "-y", "-loglevel", "error"],
                capture_output=True, timeout=15
            )
            if not os.path.exists(tmp_wav) or os.path.getsize(tmp_wav) < 1000:
                logger.warning("LipSync: FFmpeg could not extract audio (no audio track?)")
                return None

            # Read raw PCM
            import struct
            with open(tmp_wav, 'rb') as f:
                f.read(44)  # Skip WAV header
                raw = f.read()
            os.unlink(tmp_wav)

            if len(raw) < 100:
                return None

            # Parse 16-bit PCM
            n_samples = len(raw) // 2
            samples = np.frombuffer(raw[:n_samples*2], dtype=np.int16).astype(np.float32) / 32768.0

            # Compute RMS in n_windows equal windows
            chunk_size = len(samples) // n_windows
            if chunk_size < 1:
                return None

            energy = np.array([
                np.sqrt(np.mean(samples[i*chunk_size:(i+1)*chunk_size]**2))
                for i in range(n_windows)
            ])
            return energy

        except FileNotFoundError:
            logger.warning("LipSync: FFmpeg not found — skipping audio extraction")
            return None
        except Exception as e:
            logger.warning(f"LipSync: Audio extraction failed: {e}")
            return None

    def _extract_mouth_aperture(self, frames: list) -> np.ndarray:
        """Extract per-frame mouth aperture (openness) using lower-face brightness variance."""
        apertures = []
        for frame in frames:
            try:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(60, 60))
                if len(faces) == 0:
                    apertures.append(0.0)
                    continue
                fx, fy, fw, fh = faces[0]
                # Mouth region: lower 30% of face bounding box
                mouth_y = fy + int(fh * 0.65)
                mouth_h = int(fh * 0.35)
                mouth_roi = gray[mouth_y:mouth_y+mouth_h, fx:fx+fw]
                if mouth_roi.size == 0:
                    apertures.append(0.0)
                    continue
                # Laplacian variance = edge density = indicates open mouth vs closed
                lap = cv2.Laplacian(mouth_roi, cv2.CV_64F)
                apertures.append(float(np.var(lap)))
            except Exception:
                apertures.append(0.0)

        return np.array(apertures, dtype=np.float32)

    def analyze(self, video_path: str, frames: list) -> dict:
        """Full lip-sync cross-correlation analysis."""
        if len(frames) < 6:
            return {"score": 50.0, "detail": "Too few frames for lip-sync analysis"}

        n = len(frames)

        # 1. Extract audio energy windowed to match frame count
        audio_energy = self._extract_audio_energy(video_path, n)
        if audio_energy is None:
            return {
                "score": 30.0,
                "detail": "No audio track found — lip-sync analysis skipped (video-only file)"
            }

        # 2. Extract mouth aperture per frame
        mouth_aperture = self._extract_mouth_aperture(frames)

        # Normalize both signals to 0-1
        def _normalize(arr):
            mn, mx = arr.min(), arr.max()
            if mx == mn:
                return np.zeros_like(arr)
            return (arr - mn) / (mx - mn)

        audio_norm = _normalize(audio_energy[:n])
        mouth_norm = _normalize(mouth_aperture)

        # Ensure same length
        min_len = min(len(audio_norm), len(mouth_norm))
        audio_norm = audio_norm[:min_len]
        mouth_norm = mouth_norm[:min_len]

        if min_len < 4:
            return {"score": 50.0, "detail": "Insufficient aligned data for AV sync"}

        # 3. Pearson correlation at zero lag
        pearson_corr = float(np.corrcoef(audio_norm, mouth_norm)[0, 1])
        if np.isnan(pearson_corr):
            pearson_corr = 0.0

        # 4. Cross-correlation to find temporal offset
        full_xcorr = np.correlate(audio_norm - audio_norm.mean(), mouth_norm - mouth_norm.mean(), mode='full')
        lags = np.arange(-(min_len - 1), min_len)
        peak_lag = int(lags[np.argmax(np.abs(full_xcorr))])

        # 5. Score
        score = 0.0
        reasons = []

        if pearson_corr < 0.3:
            score += 65.0
            reasons.append(f"Poor audio-visual correlation ({pearson_corr:.2f}) — mouth movement does not match speech")
        elif pearson_corr < 0.5:
            score += 35.0
            reasons.append(f"Weak AV correlation ({pearson_corr:.2f}) — possible lip-sync desync")

        if abs(peak_lag) >= 3:
            score += min(abs(peak_lag) * 10.0, 50.0)
            reasons.append(f"Peak sync offset = {peak_lag} frames — audio leads/lags video significantly")

        score = float(np.clip(score, 0.0, 100.0))
        detail = "; ".join(reasons) if reasons else f"Good lip-sync (correlation={pearson_corr:.2f}, offset={peak_lag} frames)"

        logger.info(f"LipSyncAnalyzer: score={score:.1f}, corr={pearson_corr:.2f}, lag={peak_lag}")
        return {
            "score": score,
            "detail": detail,
            "pearson_correlation": round(pearson_corr, 3),
            "frame_offset": peak_lag,
        }
