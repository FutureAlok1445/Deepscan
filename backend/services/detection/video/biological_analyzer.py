import cv2
import numpy as np
import scipy.signal
from loguru import logger

class BiologicalAnalyzer:
    """
    Remote Photoplethysmography (rPPG) Deepfake Detection Engine.
    Inspired by 'FakeCatcher' (TPAMI 2020) and CVPR 2024 Biological Signal papers.
    
    Real human faces exhibit micro-color changes (hemoglobin absorption) from cardiac 
    activity. AI-generative models (GANs, Diffusion, FaceSwaps) generate frames 
    independently or auto-regressively, completely failing to synthesize a coherent, 
    periodic biological pulse.
    """
    def __init__(self):
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        logger.info("BiologicalAnalyzer (rPPG) initialized")

    def analyze_frames(self, frames: list, fps: float = 30.0) -> dict:
        """
        Extract the rPPG spatial-temporal signal and compute the heartbeat frequency.
        """
        if len(frames) < fps * 2:  # Need at least 2 seconds of video for reliable FFT
            return {
                "score": 50.0, 
                "detail": "Video too short", 
                "reasoning": f"Need at least {int(fps*2)} frames (2 seconds) to compute a meaningful physiological heartbeat via Fast Fourier Transform."
            }

        green_signals = []
        face_found = False

        # 1. Spatial-Temporal PPG Map Extraction (Green Channel)
        for frame in frames:
            try:
                # Speed optimization: Resize frame
                small_frame = cv2.resize(frame, (320, 240))
                gray = cv2.cvtColor(small_frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(40, 40))
                
                if len(faces) > 0:
                    face_found = True
                    fx, fy, fw, fh = faces[0]
                    # ROI: Upper cheeks and forehead (best for hemoglobin absorption)
                    roi = small_frame[fy + int(fh*0.1):fy + int(fh*0.8), fx + int(fw*0.2):fx + int(fw*0.8)]
                    
                    if roi.size > 0:
                        # Extract the green channel (index 1 in BGR)
                        green_channel = roi[:, :, 1]
                        # Compute the spatial mean for this frame
                        spatial_mean = np.mean(green_channel)
                        green_signals.append(spatial_mean)
                    else:
                        green_signals.append(green_signals[-1] if green_signals else 0.0)
                else:
                    # If tracking is temporarily lost, hold the last value
                    green_signals.append(green_signals[-1] if green_signals else 0.0)
            except Exception:
                green_signals.append(green_signals[-1] if green_signals else 0.0)

        if not face_found or len(green_signals) < 10:
            return {
                "score": 30.0, 
                "detail": "No face found", 
                "reasoning": "Could not lock onto a facial region to measure continuous hemoglobin absorption."
            }

        # 2. Signal Processing (rPPG Time-Series)
        signal = np.array(green_signals, dtype=np.float64)
        
        # Detrend the signal (remove static lighting changes or slow movement)
        try:
            signal = scipy.signal.detrend(signal)
            
            # Interpolate to handle potential frame drops or extreme outliers
            q1, q3 = np.percentile(signal, [5, 95])
            signal = np.clip(signal, q1, q3)
            
            # Normalize map
            signal = (signal - np.mean(signal)) / (np.std(signal) + 1e-6)
        except Exception as e:
            logger.warning(f"rPPG Detrending failed: {e}")
            return {"score": 50.0, "detail": "Signal noise", "reasoning": "Hemoglobin signal too corrupted by lighting/movement to analyze."}

        # 3. Frequency Analysis (FFT)
        N = len(signal)
        # Apply Hanning window to reduce spectral leakage
        window = np.hanning(N)
        fft_out = np.fft.rfft(signal * window)
        frequencies = np.fft.rfftfreq(N, d=1.0/fps)
        magnitude = np.abs(fft_out)
        
        # Human heart rate physiological bounds: 45 BPM to 180 BPM (0.75 Hz - 3.0 Hz)
        valid_idx = np.where((frequencies >= 0.75) & (frequencies <= 3.0))[0]
        
        if len(valid_idx) == 0:
             return {"score": 80.0, "detail": "No dominant rhythm", "reasoning": "No coherent biological frequency found within human physiological bounds (45-180 BPM)."}

        # Extract energies
        valid_magnitudes = magnitude[valid_idx]
        valid_frequencies = frequencies[valid_idx]
        
        peak_idx = np.argmax(valid_magnitudes)
        peak_freq = valid_frequencies[peak_idx]
        heart_rate_bpm = peak_freq * 60.0

        # Calculate Signal-to-Noise Ratio (SNR)
        peak_energy = valid_magnitudes[peak_idx]**2
        total_energy = np.sum(magnitude**2) + 1e-6
        snr = peak_energy / total_energy

        # --- 4. Scientific Deepfake Scoring ---
        score = 0.0
        details = []
        reasoning_list = []

        # A real human face provides a clear, dominant spike in the FFT spectrum.
        # AI generators inject uniform noise or completely flatline the frequency spectrum.
        if snr < 0.05:
            # Very low SNR -> High likelihood of generated noise
            noise_penalty = min(85.0, (0.05 - snr) * 2000.0)
            score = max(score, noise_penalty)
            details.append(f"Erratic Pulse (SNR: {snr:.3f})")
            reasoning_list.append("The spatial-temporal PPG map shows an extremely low Signal-to-Noise Ratio. No coherent biological heartbeat could be separated from the visual noise layer, a common indicator of autoregressive or diffusion-generated synthesis.")
        elif snr < 0.15:
            score = max(score, 40.0)
            details.append(f"Weak Pulse (SNR: {snr:.3f})")
            reasoning_list.append("The heartbeat signal is weak and bordering on synthetic noise.")
            
        # Unnatural BPM bounds (e.g. exactly 45.0 or 180.0 usually means the peak hit the boundary due to chaos)
        if peak_freq <= 0.8 or peak_freq >= 2.9:
            score = max(score, 60.0)
            details.append(f"Unnatural Rate ({heart_rate_bpm:.0f} BPM)")
            reasoning_list.append(f"Detected a dominant frequency of {heart_rate_bpm:.0f} BPM at the absolute bounds of human physiology. This suggests the algorithm is picking up synthetic temporal flickering rather than a true cardiac pulse.")

        score = float(np.clip(score, 0.0, 100.0))
        
        if score < 20.0:
            detail_msg = f"Authentic pulse ({heart_rate_bpm:.0f} BPM)"
            reasoning_msg = f"Detected a strong, coherent biological heartbeat signal at {heart_rate_bpm:.0f} BPM (SNR: {snr:.3f}). The underlying skin exhibits natural hemoglobin micro-color variations, strongly suggesting an authentic human subject."
        else:
            detail_msg = "; ".join(details)
            reasoning_msg = " ".join(reasoning_list)

        logger.info(f"BiologicalAnalyzer (rPPG): score={score:.1f}, BPM={heart_rate_bpm:.1f}, SNR={snr:.3f}")
        return {
            "score": score,
            "detail": detail_msg,
            "reasoning": reasoning_msg,
            "heart_rate_bpm": round(heart_rate_bpm, 1),
            "snr": round(snr, 4)
        }
