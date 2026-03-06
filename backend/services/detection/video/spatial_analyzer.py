"""
SpatialAnalyzer — Local OpenCV Frequency-Domain Analysis

Replaces the broken Hugging Face image API with a local signal-processing
approach that genuinely differs between real and AI-generated video frames.

Real camera frames:
  - Rich high-frequency content (texture, edges, noise)
  - Irregular noise distribution (non-uniform PRNU)
  - High local entropy variety (complex texture)

AI-generated frames (diffusion/GAN):
  - Smooth mid-frequency dominance (soft gradients)
  - Low standard deviation across image blocks
  - Low entropy (homogeneous regions)
  - Grid-like regularities in the FFT spectrum
"""
import cv2
import numpy as np
from loguru import logger


class SpatialAnalyzer:
    """
    Local FFT + texture analysis spatial engine.
    No external API calls. Runs entirely on the CPU.
    Returns a score 0-100 where higher = more likely AI-generated.
    """

    def __init__(self):
        logger.info("SpatialAnalyzer (Local FFT Engine) initialized.")

    async def analyze_frames(self, frames: list) -> float:
        """
        Analyze a list of keyframes and return an aggregated AI probability score (0-100).
        """
        if not frames:
            return 50.0

        frame_scores = [self._score_frame(f) for f in frames if f is not None]
        if not frame_scores:
            return 50.0

        score = float(np.mean(frame_scores))
        logger.info(f"SpatialAnalyzer: per-frame scores={[round(s,1) for s in frame_scores]}, mean={score:.1f}")
        return float(np.clip(score, 0.0, 100.0))

    def _score_frame(self, frame: np.ndarray) -> float:
        """
        Analyse a single frame and return an AI-probability score 0-100.
        """
        try:
            if frame is None or frame.size == 0:
                return 50.0

            # Ensure BGR 3-channel
            if len(frame.shape) == 2:
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif frame.shape[2] == 4:
                frame = frame[:, :, :3]

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY).astype(np.float32)
            h, w = gray.shape

            # 1. FFT: how much energy is in the high-frequency domain?
            fft = np.fft.fft2(gray)
            fft_shift = np.fft.fftshift(fft)
            magnitude = np.log1p(np.abs(fft_shift))

            cy, cx = h // 2, w // 2
            # Inner 10% = low frequency energy
            inner_r = max(h, w) // 10
            inner_mask = np.zeros((h, w), bool)
            inner_mask[cy-inner_r:cy+inner_r, cx-inner_r:cx+inner_r] = True

            total_energy = magnitude.sum() + 1e-9
            lf_energy = magnitude[inner_mask].sum()
            hf_energy = magnitude[~inner_mask].sum()
            # AI images: lf_energy >> hf_energy → high lf_ratio
            lf_ratio = lf_energy / total_energy  # 0-1: higher = more AI-like
            fft_score = lf_ratio * 100.0          # scale to 0-100

            # 2. Local block uniformity (8x8 blocks)
            # AI images have suspiciously uniform local regions
            block_stds = []
            bh, bw = max(1, h // 8), max(1, w // 8)
            for r in range(8):
                for c in range(8):
                    block = gray[r*bh:(r+1)*bh, c*bw:(c+1)*bw]
                    if block.size:
                        block_stds.append(float(block.std()))
            avg_block_std = float(np.mean(block_stds)) if block_stds else 20.0
            # Low block_std = uniform = AI. Real images ~15-35 std.
            # Map: std=0 → 100 (AI), std>=30 → 0 (real)
            uniformity_score = max(0.0, 100.0 - (avg_block_std * 3.3))

            # 3. Laplacian edge density — must use uint8 input for CV_32F
            gray_u8 = gray.astype(np.uint8)
            laplacian = cv2.Laplacian(gray_u8, cv2.CV_32F)
            edge_den = float(np.abs(laplacian).mean())
            # Low edge_den = smooth = AI. Real images typically 3-15.
            # Map: <=1 → 100, >=15 → 0
            edge_score = max(0.0, 100.0 - (edge_den * 7.0))

            # 4. Colour channel variance flatness
            # AI diffusion images have artificially balanced colour channels
            channel_stds = [float(frame[:,:,c].std()) for c in range(3)]
            ch_var = float(np.std(channel_stds))
            # Very low variance between channel stds = suspicious AI balancing
            channel_score = max(0.0, 60.0 - (ch_var * 3.0))

            # Weighted combination
            # FFT and uniformity are the most reliable signals
            combined = (
                fft_score * 0.35 +
                uniformity_score * 0.35 +
                edge_score * 0.20 +
                channel_score * 0.10
            )

            # HARSHNESS SCALER:
            # Multiply by 1.25 to make the baseline detection more sensitive to AI artifacts
            combined *= 1.25

            return float(np.clip(combined, 0.0, 100.0))

        except Exception as e:
            logger.error(f"SpatialAnalyzer frame scoring failed: {e}")
            return 50.0
