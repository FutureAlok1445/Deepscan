import cv2
import numpy as np
from loguru import logger

class NoiseAnalyzer:
    def __init__(self):
        self.target_size = (256, 256)
        
    def extract_noise_fingerprint(self, img):
        """
        Extracts high-frequency noise using Fast Fourier Transform (FFT).
        Real sensors have PRNU (Photo Response Non-Uniformity).
        Diffusion models (Sora, SDVideo) have grid-like or over-smoothed latent noise.
        """
        try:
            # Convert to grayscale and resize for consistent FFT calculation
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.resize(gray, self.target_size)
            
            # Apply FFT
            f = np.fft.fft2(gray)
            fshift = np.fft.fftshift(f)
            magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)
            
            # Create a high-pass filter mask
            rows, cols = self.target_size
            crow, ccol = rows // 2 , cols // 2
            # Block low frequencies (the center)
            mask = np.ones((rows, cols), np.uint8)
            r = 30 # radius of blocked low frequencies
            center = [crow, ccol]
            x, y = np.ogrid[:rows, :cols]
            mask_area = (x - center[0])**2 + (y - center[1])**2 <= r*r
            mask[mask_area] = 0
            
            # Apply mask and inverse FFT to get the high-frequency image
            fshift = fshift * mask
            f_ishift = np.fft.ifftshift(fshift)
            img_back = np.fft.ifft2(f_ishift)
            img_back = np.abs(img_back)
            
            return img_back
        except Exception as e:
            logger.error(f"FFT Noise Extraction failed: {e}")
            return None

    def analyze_frames(self, frames: list) -> float:
        """
        Evaluates the noise fingerprint across multiple frames.
        Returns a 'synthetic noise score' from 0 to 100.
        """
        if not frames:
            return 0.0
            
        noise_variances = []
        for frame in frames:
            noise_img = self.extract_noise_fingerprint(frame)
            if noise_img is not None:
                # Real sensors have structured, natural noise variance.
                # AI Videos often have unnaturally smooth high frequencies or structured grid artifacts.
                var = np.var(noise_img)
                noise_variances.append(var)
                
        if not noise_variances:
            return 0.0
            
        avg_var = sum(noise_variances) / len(noise_variances)
        
        # Heuristic: 
        # Real high-freq variance is typically between a certain natural threshold.
        # Too low = artificially smoothed (Diffusion).
        # Too high = grid artifacts (GANs/Up-scalers).
        
        # Normalize score (this tuning depends on exact model outputs, simple heuristic for now)
        # If variance is highly unnatural, increase penalty.
        if avg_var < 50.0: # Unnaturally smooth
            return 85.0
        elif avg_var > 3000.0: # Extreme artifacts
            return 75.0
            
        # Normal camera noise
        return 10.0
