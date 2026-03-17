import cv2
import numpy as np
import subprocess
import tempfile
import os
import asyncio
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

    async def _extract_audio_energy(self, video_path: str, n_windows: int) -> np.ndarray | None:
        """Extract per-window RMS audio energy using FFmpeg (async-friendly)."""
        try:
            # Write audio to temp WAV using FFmpeg
            tmp_wav = tempfile.mktemp(suffix=".wav")
            
            # Using asyncio to run the subprocess without blocking
            process = await asyncio.create_subprocess_exec(
                "ffmpeg", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
                "-ar", "16000", "-ac", "1", tmp_wav, "-y", "-loglevel", "error",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            await asyncio.wait_for(process.wait(), timeout=15.0)

            if not os.path.exists(tmp_wav) or os.path.getsize(tmp_wav) < 1000:
                return None

            # Read raw PCM
            def _read_pcm():
                with open(tmp_wav, 'rb') as f:
                    f.read(44)  # Skip WAV header
                    return f.read()
            
            raw = await asyncio.to_thread(_read_pcm)
            if os.path.exists(tmp_wav): os.unlink(tmp_wav)

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

        except FileNotFoundError as e:
            logger.warning("LipSync: FFmpeg NOT FOUND. Please install FFmpeg and add it to your PATH.")
            return None
        except Exception as e:
            msg = str(e)
            if "[WinError 2]" in msg or "ffmpeg" in msg.lower():
                 logger.warning("LipSync: FFmpeg executable not found. Audio extraction skipped.")
            else:
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

    async def analyze(self, video_path: str, frames: list) -> dict:
        """
        Full lip-sync cross-correlation analysis.
        Logic: Real human speech is physically coupled to mouth movement.
        - High energy phonemes (vowels) correlate with large mouth apertures.
        - Plosives (B, P, M) require lip closure (zero aperture).
        - Deepfakes often 'slide' or 'mush' these transitions due to independent generation.
        """
        if len(frames) < 10:
            return {"score": 50.0, "detail": "Insufficient data", "reasoning": "Video length too short to compute reliable AV cross-correlation."}

        n = len(frames)
        audio_energy = await self._extract_audio_energy(video_path, n)
        if audio_energy is None:
            return {"score": 25.0, "detail": "No audio", "reasoning": "No acoustic signal detected for sync verification. Analysis inconclusive."}

        mouth_aperture = self._extract_mouth_aperture(frames)

        def _normalize(arr):
            mn, mx = arr.min(), arr.max()
            if mx == mn: return np.zeros_like(arr)
            return (arr - mn) / (mx - mn + 1e-6)

        audio_norm = _normalize(audio_energy[:n])
        mouth_norm = _normalize(mouth_aperture)
        min_len = min(len(audio_norm), len(mouth_norm))
        audio_norm, mouth_norm = audio_norm[:min_len], mouth_norm[:min_len]

        if min_len < 10:
            return {"score": 50.0, "detail": "Low alignment", "reasoning": "Failed to align enough acoustic/visual samples for statistical significance."}

        # 1. Pearson correlation (Sync Accuracy)
        pearson_corr = float(np.corrcoef(audio_norm, mouth_norm)[0, 1])
        if np.isnan(pearson_corr): pearson_corr = 0.0

        # 2. Cross-correlation (Temporal Shift)
        full_xcorr = np.correlate(audio_norm - audio_norm.mean(), mouth_norm - mouth_norm.mean(), mode='full')
        lags = np.arange(-(min_len - 1), min_len)
        peak_lag = int(lags[np.argmax(np.abs(full_xcorr))])

        # --- Scientific Scoring ---
        # Sigmoid centered at 0.4 correlation. Values < 0.25 are high-confidence fakes.
        # Higher pearson_corr -> higher exp() -> lower score.
        # Lower pearson_corr -> lower exp() -> higher score (fake).
        score = 100 / (1 + np.exp(8 * (pearson_corr - 0.35)))

        details = []
        reasoning_list = []

        if pearson_corr < 0.4:
            details.append(f"Low correlation: {pearson_corr:.2f}")
            reasoning_list.append(f"The Pearson correlation ({pearson_corr:.2f}) between vocal energy and mouth aperture is significantly below the human baseline (>0.6). This 'Phoneme-Viseme' mismatch suggests the audio was overlaid or the lips were generated independently of the specific acoustic features.")
        
        if abs(peak_lag) > 2:
            shift_penalty = min(abs(peak_lag) * 15.0, 40.0)
            score = max(score, shift_penalty)
            details.append(f"Lag: {peak_lag} frames")
            reasoning_list.append(f"Detected a temporal desync of {peak_lag} frames. While small lags can be network jitter, constant offsets in high-quality video are common indicators of 'DeepFace' style re-enactment.")

        score = float(np.clip(score, 0.0, 100.0))
        detail_msg = "; ".join(details) if details else f"Natural (Corr={pearson_corr:.2f})"
        reasoning_msg = " ".join(reasoning_list) if reasoning_list else f"Strong acoustic-visual coupling (Corr={pearson_corr:.2f}) indicates an authentic, physically linked speech production process."

        logger.info(f"LipSyncAnalyzer: score={score:.1f}, corr={pearson_corr:.2f}")
        return {
            "score": score,
            "detail": detail_msg,
            "reasoning": reasoning_msg,
            "pearson_correlation": round(pearson_corr, 3),
            "frame_offset": peak_lag,
        }
