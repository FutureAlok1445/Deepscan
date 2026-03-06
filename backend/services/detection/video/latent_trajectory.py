import torch
import torch.nn as nn
import torchvision.models.video as models
import cv2
import numpy as np
from scipy.spatial.distance import cosine
from loguru import logger

class LatentTrajectoryForensics:
    def __init__(self):
        try:
            self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
            # Load R(2+1)D-18 (Kinetics-400 Pre-trained)
            self.model = models.r2plus1d_18(pretrained=True).to(self.device)
            self.model.eval()
            
            # Strip classifier -> Output is 512-dim embedding
            self.feature_extractor = nn.Sequential(*list(self.model.children())[:-1])
            
            # Normalization (Kinetics-400 stats)
            self.mean = torch.tensor([0.43216, 0.394666, 0.37645]).view(3, 1, 1, 1).to(self.device)
            self.std = torch.tensor([0.22803, 0.22145, 0.216989]).view(3, 1, 1, 1).to(self.device)
            self.is_loaded = True
            logger.info("LatentTrajectoryForensics engine (LTCA) loaded successfully")
        except Exception as e:
            self.is_loaded = False
            logger.error(f"Failed to load LTCA engine: {e}")

    def extract_sliding_windows(self, video_path, window_size=16, stride=8):
        """
        Extracts overlapping video volumes to track evolution over time.
        """
        try:
            cap = cv2.VideoCapture(video_path)
            frames = []
            while True:
                ret, frame = cap.read()
                if not ret: break
                frame = cv2.resize(frame, (112, 112))
                frames.append(frame)
            cap.release()
            
            if len(frames) < window_size:
                return None

            # Create sliding windows
            clips = []
            for i in range(0, len(frames) - window_size + 1, stride):
                clip = frames[i : i + window_size]
                # Convert to Tensor (C, T, H, W)
                tensor = torch.tensor(np.array(clip), dtype=torch.float32).permute(3, 0, 1, 2)
                tensor = tensor.to(self.device) / 255.0
                tensor = (tensor - self.mean) / self.std
                clips.append(tensor)
                
            # Stack into batch: (Batch_Size, 3, 16, 112, 112)
            return torch.stack(clips)
        except Exception as e:
            logger.error(f"Error extracting sliding windows: {e}")
            return None

    def analyze_trajectory(self, video_path):
        if not self.is_loaded:
             return {"is_fake": False, "confidence": 0, "reason": "Engine not loaded", "trajectory_plot": []}

        batch = self.extract_sliding_windows(video_path)
        if batch is None:
             return {"is_fake": False, "confidence": 0, "reason": "Video too short", "trajectory_plot": []}

        try:
            with torch.no_grad():
                # Get embeddings for ALL windows at once
                # Output: (Batch_Size, 512)
                embeddings = self.feature_extractor(batch).squeeze(-1).squeeze(-1).squeeze(-1)
                embeddings = embeddings.cpu().numpy()

            # --- GEOMETRIC ANALYSIS ---
            
            velocities = []
            curvatures = []
            
            # We need at least 3 points to measure curvature
            if len(embeddings) < 3:
                 return {"is_fake": False, "confidence": 0, "reason": "Video too short for trajectory analysis", "trajectory_plot": []}

            for i in range(len(embeddings) - 2):
                # Point A, B, C in latent space
                p1, p2, p3 = embeddings[i], embeddings[i+1], embeddings[i+2]
                
                # Vector 1 (Movement from A to B)
                v1 = p2 - p1
                # Vector 2 (Movement from B to C)
                v2 = p3 - p2
                
                # 1. Latent Velocity (Magnitude of change)
                # AI often has "Sudden Jumps" (High Velocity) or "Freezes" (Zero Velocity)
                velocity = np.linalg.norm(v1)
                velocities.append(float(velocity))
                
                # 2. Latent Curvature (Cosine Similarity of directions)
                # Real motion has momentum (v1 and v2 point in similar directions).
                # AI motion jitters (v1 and v2 can be orthogonal or opposite).
                # 1.0 = Straight line, 0.0 = 90 degree turn, -1.0 = U-turn
                similarity = 1 - cosine(v1, v2) 
                
                # Handle NaNs if vectors are zero
                if np.isnan(similarity):
                    similarity = 0.0
                    
                curvatures.append(float(similarity))

            # --- THE VERDICT ---
            
            avg_velocity = float(np.mean(velocities))
            avg_curvature = float(np.mean(curvatures))
            velocity_variance = float(np.var(velocities))

            # HEURISTIC LOGIC (Zero False Positives Rethink):
            # Handheld cameras, fast action, and compression cause natural jitter.
            # We must only flag mathematically impossible physics (e.g. complete vector collapse).
            
            is_fake = False
            confidence = 0
            reason = "Natural Physics or minor camera shake."
            
            if avg_curvature < 0.25:
                # The motion vector is completely chaotic/random (Highly unusual for real video)
                is_fake = True
                confidence = 65 # Reduced from 92: Physics alone does not prove a deepfake
                reason = "GEOMETRIC ANOMALY: Severe latent trajectory collapse detected."
            
            elif velocity_variance > 8.0:
                # The object is teleporting between frames
                is_fake = True
                confidence = 50 # Reduced from 85
                reason = "TEMPORAL ANOMALY: Impossibly high velocity variance."

            return {
                "is_fake": is_fake,
                "confidence": confidence,
                "reason": reason,
                "curvature_score": round(avg_curvature, 2),
                "velocity_variance": round(velocity_variance, 2),
                "trajectory_plot": [round(c, 3) for c in curvatures] # Send this array to Frontend
            }
        except Exception as e:
            logger.error(f"Error during trajectory analysis: {e}")
            return {"is_fake": False, "confidence": 0, "reason": f"Analysis failed: {e}", "trajectory_plot": []}
