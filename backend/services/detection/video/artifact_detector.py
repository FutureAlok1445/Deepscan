import cv2
import numpy as np
from loguru import logger

class ArtifactDetector:
    """
    Scans video frames for low-level Deepfake artifacts:
    Phase 1 (Original): Mask blending boundaries, color mismatch, blockiness
    Phase 2 (NEW): DCT checkerboard fingerprinting (GAN), noise residue autocorrelation (Diffusion)
    """
    def __init__(self):
        logger.info("ArtifactDetector initialized (Laplacian + DCT + Noise Residue)")

    def analyze_frames(self, frames: list) -> float:
        """Analyzes a sequence of frames and returns an artifact probability score (0-100)."""
        if not frames:
            return 50.0

        scores = []
        for frame in frames:
            if frame is None or frame.size == 0:
                continue
            scores.append(self._score_frame(frame))
            
        if not scores:
            return 50.0

        final_score = float(np.mean(scores))
        logger.info(f"ArtifactDetector score: {final_score:.1f}/100")
        return final_score

    def _score_frame(self, frame: np.ndarray) -> float:
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # ─── 1. Edge Blur/Sharpness Mismatch (Laplacian) ───
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            variance = np.var(laplacian)
            if variance < 30:
                blur_penalty = 80.0
            elif variance > 1500:
                blur_penalty = 60.0
            else:
                blur_penalty = 10.0

            # ─── 2. GAN Checkerboard via DCT ───
            dct_penalty = self._dct_checkerboard_score(gray)

            # ─── 3. Blockiness / Grid Artifacts ───
            h, w = gray.shape
            if h > 8 and w > 8:
                diff_h = np.abs(gray[:-8, :].astype(float) - gray[8:, :].astype(float)).mean()
                diff_v = np.abs(gray[:, :-8].astype(float) - gray[:, 8:].astype(float)).mean()
                grid_score = (diff_h + diff_v) / 2
                block_penalty = 70.0 if grid_score < 2.0 else 15.0
            else:
                block_penalty = 0.0

            # ─── 4. Color Space Inconsistencies (YCbCr chroma) ───
            ycbcr = cv2.cvtColor(frame, cv2.COLOR_BGR2YCrCb)
            cb_var = float(np.var(ycbcr[:, :, 1]))
            cr_var = float(np.var(ycbcr[:, :, 2]))
            color_penalty = 85.0 if (cb_var < 5.0 or cr_var < 5.0) else 10.0

            # ─── 5. Diffusion Noise Residue Autocorrelation ───
            residue_penalty = self._diffusion_residue_score(gray)

            # Weighted aggregate — DCT and residue are the strongest new signals
            combined = (
                blur_penalty   * 0.20 +
                dct_penalty    * 0.30 +
                block_penalty  * 0.15 +
                color_penalty  * 0.15 +
                residue_penalty * 0.20
            )
            return float(np.clip(combined, 0.0, 100.0))
            
        except Exception as e:
            logger.error(f"Artifact frame scoring failed: {e}")
            return 50.0

    def _dct_checkerboard_score(self, gray: np.ndarray) -> float:
        """
        Detect GAN checkerboard artifacts via 2D DCT on 8x8 blocks.
        GAN transposed-convolution upsampling leaves energy spikes at block boundaries
        in the high-freq DCT coefficients (positions [0,4], [4,0], [4,4]).
        """
        try:
            h, w = gray.shape
            # Only use the center crop for faces
            ch, cw = h // 4, w // 4
            center = gray[ch:h-ch, cw:w-cw].astype(np.float32)
            ch2, cw2 = center.shape

            # Restrict to blocks that fit
            n_bh = ch2 // 8
            n_bw = cw2 // 8
            if n_bh < 2 or n_bw < 2:
                return 20.0

            high_freq_energies = []
            for i in range(n_bh):
                for j in range(n_bw):
                    block = center[i*8:(i+1)*8, j*8:(j+1)*8]
                    dct_block = cv2.dct(block)
                    # High frequency = bottom-right coefficients (rows/cols 4-7)
                    hf = dct_block[4:, 4:]
                    # Low frequency = top-left
                    lf = dct_block[:4, :4]
                    lf_energy = np.sum(lf**2) + 1e-6
                    hf_energy = np.sum(hf**2)
                    ratio = hf_energy / lf_energy
                    high_freq_energies.append(ratio)

            mean_ratio = float(np.mean(high_freq_energies))
            std_ratio = float(np.std(high_freq_energies))

            # GAN artifact pattern: blocks have uniformly high HF energy ratio (structured, not random)
            # Real images: HF energy is sparse and varies greatly across blocks
            if mean_ratio > 0.15 and std_ratio < 0.05:
                # Uniform high HF energy = GAN checkerboard
                return 80.0
            elif mean_ratio > 0.10:
                return 40.0
            else:
                return 10.0
        except Exception:
            return 20.0

    def _diffusion_residue_score(self, gray: np.ndarray) -> float:
        """
        Detect diffusion model (Sora/DALL-E) noise via noise residue autocorrelation.
        Subtract Gaussian blur to isolate noise. Real camera noise is i.i.d. random.
        Diffusion model noise has spatial structure (correlates at short distances).
        """
        try:
            # Extract noise residue
            blurred = cv2.GaussianBlur(gray.astype(np.float32), (5, 5), 0)
            residue = gray.astype(np.float32) - blurred

            # Compute 2D autocorrelation at lag (1,0) and (0,1)
            h, w = residue.shape
            if h < 4 or w < 4:
                return 20.0

            # Lag-1 autocorrelation in X
            corr_x = float(np.corrcoef(residue[:, :-1].flatten(), residue[:, 1:].flatten())[0, 1])
            # Lag-1 autocorrelation in Y
            corr_y = float(np.corrcoef(residue[:-1, :].flatten(), residue[1:, :].flatten())[0, 1])

            if np.isnan(corr_x): corr_x = 0.0
            if np.isnan(corr_y): corr_y = 0.0

            mean_corr = (abs(corr_x) + abs(corr_y)) / 2.0

            # Real camera noise: |correlation| < 0.05 (nearly independent)
            # Diffusion noise: |correlation| > 0.15 (structured texture)
            if mean_corr > 0.25:
                return 85.0
            elif mean_corr > 0.15:
                return 55.0
            elif mean_corr > 0.08:
                return 30.0
            else:
                return 5.0
        except Exception:
            return 20.0
