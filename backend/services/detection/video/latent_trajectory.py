from loguru import logger

HAS_TORCH = False
HAS_CV2 = False

try:
    import torch
    import torch.nn as nn
    import torchvision.models.video as models
    HAS_TORCH = True
except ImportError:
    logger.warning("torch/torchvision not installed — LatentTrajectoryForensics disabled")

try:
    import cv2
    import numpy as np
    from scipy.spatial.distance import cosine
    HAS_CV2 = True
except ImportError:
    logger.warning("cv2/numpy/scipy not installed — LatentTrajectoryForensics disabled")
    # Provide minimal numpy stub so np.ndarray type hints don't crash
    try:
        import numpy as np
    except ImportError:
        import types
        np = types.SimpleNamespace(ndarray=object, array=lambda *a, **k: [],
                                   mean=lambda *a: 0, var=lambda *a: 0,
                                   linalg=types.SimpleNamespace(norm=lambda *a: 0),
                                   isnan=lambda x: False)


class LatentTrajectoryForensics:
    def __init__(self):
        self.is_loaded = False
        if not HAS_TORCH or not HAS_CV2:
            logger.warning("LatentTrajectoryForensics: Missing deps — running in fallback mode")
            return
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

    def extract_from_frames(self, frames, window_size=16, stride=4):
        """
        Extracts overlapping video volumes from pre-decoded frames (memory-efficient).
        """
        if not self.is_loaded:
            return None
        try:
            if len(frames) < window_size:
                return None

            clips = []
            for i in range(0, len(frames) - window_size + 1, stride):
                clip = []
                for f in frames[i : i + window_size]:
                    if f.shape[0] != 112 or f.shape[1] != 112:
                        f = cv2.resize(f, (112, 112))
                    clip.append(f)
                
                # Convert to Tensor (C, T, H, W)
                tensor = torch.from_numpy(np.array(clip)).to(torch.float32).permute(3, 0, 1, 2)
                tensor = tensor / 255.0
                tensor = (tensor - self.mean) / self.std
                clips.append(tensor)
                
            if not clips: return None
            return torch.stack(clips).to(self.device)
        except Exception as e:
            logger.error(f"Error extracting windows from frames: {e}")
            return None

    def analyze_trajectory(self, video_path_or_frames):
        """
        Can accept a video_path or a list of numpy frames.
        """
        _fallback = {"is_fake": False, "confidence": 0, "reason": "Engine not loaded", "trajectory_plot": []}
        
        if not self.is_loaded:
            return _fallback

        if isinstance(video_path_or_frames, str):
            cap = cv2.VideoCapture(video_path_or_frames)
            frames = []
            while len(frames) < 128:
                ret, f = cap.read()
                if not ret: break
                frames.append(f)
            cap.release()
            batch = self.extract_from_frames(frames)
        else:
            batch = self.extract_from_frames(video_path_or_frames)
        
        if batch is None:
             return {"is_fake": False, "confidence": 0, "reason": "Video too short", "trajectory_plot": []}

        try:
            with torch.no_grad():
                embeddings = self.feature_extractor(batch).squeeze(-1).squeeze(-1).squeeze(-1)
                embeddings = embeddings.cpu().numpy()

            velocities = []
            curvatures = []
            
            if len(embeddings) < 3:
                 return {"is_fake": False, "confidence": 0, "reason": "Video too short for trajectory analysis", "trajectory_plot": []}

            for i in range(len(embeddings) - 2):
                p1, p2, p3 = embeddings[i], embeddings[i+1], embeddings[i+2]
                v1 = p2 - p1
                v2 = p3 - p2
                
                velocity = np.linalg.norm(v1)
                velocities.append(float(velocity))
                
                similarity = 1 - cosine(v1, v2) 
                if np.isnan(similarity):
                    similarity = 0.0
                curvatures.append(float(similarity))

            avg_velocity = float(np.mean(velocities))
            avg_curvature = float(np.mean(curvatures))
            velocity_variance = float(np.var(velocities))

            is_fake = False
            confidence = 0
            reason = "Natural Physics or minor camera shake."
            
            if avg_curvature < 0.25:
                is_fake = True
                confidence = 65
                reason = "GEOMETRIC ANOMALY: Severe latent trajectory collapse detected."
            
            elif velocity_variance > 8.0:
                is_fake = True
                confidence = 50
                reason = "TEMPORAL ANOMALY: Impossibly high velocity variance."

            return {
                "is_fake": is_fake,
                "confidence": confidence,
                "reason": reason,
                "curvature_score": round(avg_curvature, 2),
                "velocity_variance": round(velocity_variance, 2),
                "trajectory_plot": [round(c, 3) for c in curvatures]
            }
        except Exception as e:
            logger.error(f"Error during trajectory analysis: {e}")
            return {"is_fake": False, "confidence": 0, "reason": f"Analysis failed: {e}", "trajectory_plot": []}
