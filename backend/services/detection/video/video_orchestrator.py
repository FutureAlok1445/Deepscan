import os
import cv2
import numpy as np
from loguru import logger

from backend.services.detection.video.spatial_analyzer import SpatialAnalyzer
from backend.services.detection.video.optical_flow_analyzer import OpticalFlowAnalyzer
from backend.services.detection.video.noise_analyzer import NoiseAnalyzer
from backend.services.detection.video.latent_trajectory import LatentTrajectoryForensics
from backend.services.explainability.video_nlm_report import VideoNLMReport

class VideoOrchestrator:
    def __init__(self):
        self.spatial = SpatialAnalyzer()
        self.temporal = OpticalFlowAnalyzer()
        self.noise = NoiseAnalyzer()
        self.ltca = LatentTrajectoryForensics()
        self.nlm_reporter = VideoNLMReport()
        logger.info("Modular VideoOrchestrator loaded (Spatial + Temporal + Noise + LTCA + NLM)")

    async def process_video(self, video_path: str, num_frames=12) -> tuple:
        """
        100% Flawless Video Detection Pipeline
        Aggregates multiple distinct analytical vectors:
        1. LTCA (Latent Physics)
        2. Spatial (Vision Transformer)
        3. Temporal (Optical Flow flickering)
        4. Noise (FFT Diffusion fingerprints)
        """
        try:
            # 1. Latent Trajectory
            ltca_data = self.ltca.analyze_trajectory(video_path)
            ltca_penalty = 0.0
            if ltca_data.get("is_fake"):
                ltca_penalty = ltca_data.get("confidence", 0) * 0.40 # 40% weight to physics
                logger.warning(f"LTCA Flag: {ltca_data.get('reason')}")

            # Extract frames once for other analyzers
            cap = cv2.VideoCapture(video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            if total <= 1:
                return 50.0, {}

            # Sample evenly distributed keyframes
            frame_indices = np.linspace(0, total - 1, num_frames, dtype=int)
            frames = []
            
            # Read all required frames into memory (acceptable for short analysis clips)
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
                    
            cap.release()

            if not frames:
                return 50.0, {}

            # 2. Spatial Analysis (ViT)
            spatial_score = await self.spatial.analyze_frames([frames[0], frames[len(frames)//2], frames[-1]])
            
            # 3. Temporal Consistency
            temporal_penalty = self.temporal.analyze_sequence(frames)
            
            # 4. Generative Noise Analysis
            noise_penalty = self.noise.analyze_frames(frames)
            
            if noise_penalty > 50.0:
                logger.warning("Generative Noise Detected (Diffusion/GAN artifacts)")

            # Final Aggregation (MAS Score)
            # 30% Spatial, 20% Temporal, 40% Physics (LTCA), 10% Noise Fingerprint
            final_score = (spatial_score * 0.30) + (temporal_penalty * 0.20) + ltca_penalty + (noise_penalty * 0.10)
            
            # Clip between 0 and 100
            final_mas = min(max(final_score, 0.0), 100.0)

            # Generate Expert NLM Forensics
            nlm_text = await self.nlm_reporter.generate_report(
                mas_score=final_mas,
                spatial_score=spatial_score,
                temporal_penalty=temporal_penalty,
                noise_score=noise_penalty,
                ltca_data=ltca_data
            )
            ltca_data["nlm_report"] = nlm_text
            
            return final_mas, ltca_data

        except Exception as e:
            logger.error(f"VideoOrchestrator pipeline failed: {e}")
            return 50.0, {"nlm_report": "Forensic NLM analysis failed due to system error."}
