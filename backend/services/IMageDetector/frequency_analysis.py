from loguru import logger

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False

class FrequencyAnalyzer:
    """
    Layer 6: Detects GAN artifacts in the frequency domain using 2D FFT.
    Provides Frequency Score.
    """
    def __init__(self):
        pass

    def analyze(self, image_path: str) -> dict:
        result = {
            "score_frequency": 50.0,
            "details": []
        }
        
        if not HAS_CV2:
            result["score_frequency"] = 90.0
            result["details"].append("OpenCV/NumPy not available. Using neutral frequency score.")
            return result
        
        try:
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                raise ValueError("Could not read grayscale for FrequencyAnalyzer")
                
            f_transform = np.fft.fft2(image)
            f_shift = np.fft.fftshift(f_transform)
            magnitude_spectrum = 20 * np.log(np.abs(f_shift) + 1e-8)
            
            rows, cols = image.shape
            crow, ccol = rows // 2, cols // 2
            
            mask_size = 30
            magnitude_spectrum[crow - mask_size:crow + mask_size, ccol - mask_size:ccol + mask_size] = 0
            
            high_freq_energy = np.mean(magnitude_spectrum[magnitude_spectrum > 0])
            
            if high_freq_energy > 230:
                result["score_frequency"] = 30.0
                result["details"].append(f"Abnormal high-frequency spectrum detected (Energy: {high_freq_energy:.1f}). Possible GAN artifact.")
            elif high_freq_energy < 150:
                result["score_frequency"] = 40.0
                result["details"].append(f"Unusually low high-frequency spectrum. Possible heavy blurring/diffusion model.")
            else:
                result["score_frequency"] = 90.0
                
        except Exception as e:
            logger.error(f"Error in frequency analysis: {e}")
            result["score_frequency"] = 90.0
            
        return result

frequency_analyzer = FrequencyAnalyzer()
