import cv2
import numpy as np

class OpticalFlowAnalyzer:
    def __init__(self):
        pass

    def calculate_ssim(self, i1, i2):
        """Calculate Structural Similarity Index between two frames."""
        try:
            # Simple SSIM-like check using mean squared error
            i1 = cv2.cvtColor(i1, cv2.COLOR_BGR2GRAY)
            i2 = cv2.cvtColor(i2, cv2.COLOR_BGR2GRAY)
            err = np.sum((i1.astype("float") - i2.astype("float")) ** 2)
            err /= float(i1.shape[0] * i1.shape[1])
            return 1.0 / (1.0 + err) # Normalized 0-1
        except Exception:
            return 1.0

    def calculate_flow_variance(self, prev_frame, next_frame):
        """Analyze optical flow to detect unnatural motion (common in Higgsfield/Sora)."""
        try:
            prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
            next_gray = cv2.cvtColor(next_frame, cv2.COLOR_BGR2GRAY)
            flow = cv2.calcOpticalFlowFarneback(prev_gray, next_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)
            mag, ang = cv2.cartToPolar(flow[..., 0], flow[..., 1])
            # High variance in magnitude often indicates AI 'morphing' or flickering
            return float(np.var(mag))
        except Exception:
            return 0.0

    def analyze_sequence(self, frames: list) -> float:
        """
        Analyzes a sequence of frames for temporal fluctuations.
        Returns a penalty score based on motion anomalies.
        """
        if len(frames) < 2:
            return 0.0
            
        temporal_fluctuations = []
        for i in range(1, len(frames)):
            flow_var = self.calculate_flow_variance(frames[i-1], frames[i])
            temporal_fluctuations.append(flow_var)
            
        if temporal_fluctuations:
            avg_fluctuation = sum(temporal_fluctuations) / len(temporal_fluctuations)
            # Cap the penalty
            return min(avg_fluctuation, 40.0)
            
        return 0.0
