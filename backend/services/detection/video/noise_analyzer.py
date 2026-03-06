import cv2
import numpy as np
from loguru import logger

class NoiseAnalyzer:
    """
    Analyzes the noise signature in video frames to detect AI generation.
    Phase 1 (Original): FFT spectral flatness — diffusion models create unnaturally
    smooth or structured frequency spectra.
    Phase 2 (NEW): Multi-level wavelet decomposition to isolate HH diagonal bands.
    AI models leave structured, correlated energy in the diagonal HH wavelet subband
    while real camera PRNU (Photo Response Non-Uniformity) is spatially independent.
    """
    def __init__(self):
        logger.info("NoiseAnalyzer initialized (FFT + Wavelet HH analysis)")

    def analyze_frames(self, frames: list) -> float:
        """Returns a noise-based deepfake probability score 0–100."""
        if not frames:
            return 50.0

        scores = []
        for frame in frames:
            if frame is None or frame.size == 0:
                continue
            scores.append(self._score_frame(frame))

        if not scores:
            return 50.0

        result = float(np.mean(scores))
        logger.info(f"NoiseAnalyzer score: {result:.1f}/100")
        return result

    def _score_frame(self, frame: np.ndarray) -> float:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)

            fft_penalty   = self._fft_score(gray)
            wavelet_score = self._wavelet_hh_score(gray)
            prnu_score    = self._prnu_uniformity_score(frame)

            # Combined: wavelet is most sensitive for modern diffusion models
            combined = fft_penalty * 0.30 + wavelet_score * 0.45 + prnu_score * 0.25
            return float(np.clip(combined, 0.0, 100.0))
        except Exception as e:
            logger.error(f"NoiseAnalyzer frame scoring failed: {e}")
            return 50.0

    def _fft_score(self, gray: np.ndarray) -> float:
        """Original FFT-based analysis (retained for ensemble diversity)."""
        try:
            f = np.fft.fft2(gray)
            fshift = np.fft.fftshift(f)
            magnitude = np.abs(fshift)
            log_mag = np.log1p(magnitude)
            variance = float(np.var(log_mag))

            # Diffusion over-smoothing: very low variance
            if variance < 5.0:
                return 85.0
            # Unnaturally structured (GAN grid noise): very uniform spectrum
            elif variance < 15.0:
                return 50.0
            # Normal natural image spectrum: high variance
            else:
                return 10.0
        except Exception:
            return 50.0

    def _wavelet_hh_score(self, gray: np.ndarray) -> float:
        """
        Multi-level Haar wavelet decomposition (manual implementation, no pywt needed).
        Analyzes the HH (diagonal high-frequency) subband at level 2.
        Real camera sensors: HH energy is spatially random (low autocorrelation).
        AI diffusion models: HH energy has structured texture (high autocorrelation).
        """
        try:
            h, w = gray.shape
            if h < 8 or w < 8:
                return 30.0

            # Manual 2D Haar wavelet — level 1
            def haar_2d(img):
                """Single-level Haar DWT returning (LL, LH, HL, HH) subbands."""
                h, w = img.shape
                h2, w2 = h // 2 * 2, w // 2 * 2  # ensure even
                img = img[:h2, :w2]
                # Horizontal pass
                lo = (img[:, 0::2] + img[:, 1::2]) / 2.0
                hi = (img[:, 0::2] - img[:, 1::2]) / 2.0
                # Vertical pass on low
                LL = (lo[0::2, :] + lo[1::2, :]) / 2.0
                LH = (lo[0::2, :] - lo[1::2, :]) / 2.0
                # Vertical pass on high
                HL = (hi[0::2, :] + hi[1::2, :]) / 2.0
                HH = (hi[0::2, :] - hi[1::2, :]) / 2.0
                return LL, LH, HL, HH

            # Level 1
            LL1, LH1, HL1, HH1 = haar_2d(gray)
            # Level 2 on LL1
            LL2, LH2, HL2, HH2 = haar_2d(LL1)

            # Analyze HH2 (diagonal detail at level 2)
            hh = HH2.flatten()
            if len(hh) < 16:
                return 30.0

            # Autocorrelation at lag 1 — structured AI noise is correlated
            corr = float(np.corrcoef(hh[:-1], hh[1:])[0, 1])
            if np.isnan(corr):
                corr = 0.0

            # Energy ratio between HH bands
            hh1_energy = float(np.mean(HH1**2)) + 1e-6
            hh2_energy = float(np.mean(HH2**2)) + 1e-6
            band_ratio = hh2_energy / hh1_energy

            # Real camera: |corr| ≈ 0.0–0.05, band_ratio ≈ 0.5–0.9
            # Diffusion model: |corr| > 0.15, band_ratio < 0.3 (too smooth at fine scales)
            score = 0.0
            if abs(corr) > 0.20:
                score += 60.0
            elif abs(corr) > 0.12:
                score += 35.0

            if band_ratio < 0.25:
                score += 40.0   # Abnormally low fine-scale energy = over-smoothed
            elif band_ratio > 1.8:
                score += 30.0   # Abnormally high = GAN amplification

            return float(np.clip(score, 0.0, 100.0))
        except Exception:
            return 30.0

    def _prnu_uniformity_score(self, frame: np.ndarray) -> float:
        """
        Photo Response Non-Uniformity (PRNU) check.
        Real cameras: each sensor has unique per-pixel gain — creates fixed-pattern noise.
        AI: pixels generated independently, no PRNU — noise field is uniform.
        We estimate PRNU by analyzing channel-to-channel noise correlation.
        """
        try:
            b, g, r = cv2.split(frame.astype(np.float32))

            def _noise(ch):
                blurred = cv2.GaussianBlur(ch, (3, 3), 0)
                return ch - blurred

            nb, ng, nr = _noise(b), _noise(g), _noise(r)

            corr_br = float(np.corrcoef(nb.flatten(), nr.flatten())[0, 1])
            corr_bg = float(np.corrcoef(nb.flatten(), ng.flatten())[0, 1])
            if np.isnan(corr_br): corr_br = 0.0
            if np.isnan(corr_bg): corr_bg = 0.0

            mean_channel_corr = (abs(corr_br) + abs(corr_bg)) / 2.0

            # Real cameras: cross-channel noise has weak correlation (≈0.05–0.2) due to demosaicing
            # AI: no PRNU → channels are INDEPENDENT (correlation ≈ 0) OR perfectly correlated (≈ 1)
            if mean_channel_corr < 0.03:
                return 70.0  # Too independent — no camera noise pattern
            elif mean_channel_corr > 0.80:
                return 60.0  # Too correlated — global AI texture
            else:
                return 5.0   # Natural camera PRNU range
        except Exception:
            return 30.0
