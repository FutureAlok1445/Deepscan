import os
import cv2
import numpy as np
from loguru import logger

from backend.services.detection.video.spatial_analyzer import SpatialAnalyzer
from backend.services.detection.video.optical_flow_analyzer import OpticalFlowAnalyzer
from backend.services.detection.video.noise_analyzer import NoiseAnalyzer
from backend.services.detection.video.latent_trajectory import LatentTrajectoryForensics
from backend.services.detection.video.artifact_detector import ArtifactDetector
from backend.services.detection.video.blink_analyzer import BlinkAnalyzer
from backend.services.detection.video.face_mesh_analyzer import FaceMeshAnalyzer
from backend.services.detection.video.eye_reflection_analyzer import EyeReflectionAnalyzer
from backend.services.detection.video.lip_sync_analyzer import LipSyncAnalyzer
from backend.services.explainability.video_nlm_report import VideoNLMReport

class VideoOrchestrator:
    def __init__(self):
        self.spatial = SpatialAnalyzer()
        self.temporal = OpticalFlowAnalyzer()
        self.noise = NoiseAnalyzer()
        self.ltca = LatentTrajectoryForensics()
        self.artifact_scanner = ArtifactDetector()
        # Phase 2 — Advanced engines
        self.blink = BlinkAnalyzer()
        self.face_mesh = FaceMeshAnalyzer()
        self.eye_reflection = EyeReflectionAnalyzer()
        self.lip_sync = LipSyncAnalyzer()
        self.nlm_reporter = VideoNLMReport()
        logger.info("VideoOrchestrator loaded — 9 detection engines active")

    async def process_video(self, video_path: str, num_frames=16) -> tuple:
        """
        Full-spectrum video detection pipeline.
        Engines:
          Classic:  LTCA (Physics), Spatial (ViT), Temporal (Optical Flow), Noise (FFT+Wavelet+PRNU), Artifact (DCT+Residue)
          Advanced: Eye Blink (EAR), Face Mesh (LK), Eye Reflection, Lip-Sync (AV Cross-Corr)
        """
        try:
            # ── 1. LTCA Physics Analysis ──
            ltca_data = self.ltca.analyze_trajectory(video_path)
            if ltca_data.get("is_fake"):
                logger.warning(f"LTCA Flag: {ltca_data.get('reason')}")

            # ── 2. Frame Extraction ──
            cap = cv2.VideoCapture(video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

            if total <= 1:
                logger.warning(f"VideoOrchestrator aborted: fewer than 2 frames in {video_path}")
                cap.release()
                return 50.0, {
                    "nlm_report": "Deepscan aborted: The video contains fewer than 2 readable frames. Try re-encoding as H.264 MP4."
                }, []

            frame_indices = np.linspace(0, total - 1, num_frames, dtype=int)
            frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    frames.append(frame)
            cap.release()

            if not frames:
                return 50.0, {}, []

            # ── 3. Classic Engines ──
            spatial_score = await self.spatial.analyze_frames([frames[0], frames[len(frames)//2], frames[-1]])
            temporal_penalty = self.temporal.analyze_sequence(frames)
            noise_penalty = self.noise.analyze_frames(frames)
            artifact_penalty = self.artifact_scanner.analyze_frames(frames)

            # ── 4. Advanced Engines ──
            blink_result   = self.blink.analyze_frames(frames, fps=fps)
            mesh_result    = self.face_mesh.analyze_frames(frames)
            reflect_result = self.eye_reflection.analyze_frames(frames)
            sync_result    = self.lip_sync.analyze(video_path, frames)

            blink_score   = blink_result.get("score", 50.0)
            mesh_score    = mesh_result.get("score", 50.0)
            reflect_score = reflect_result.get("score", 50.0)
            sync_score    = sync_result.get("score", 50.0)

            # ── 5. LTCA weight contribution ──
            ltca_weight = (ltca_data.get("confidence", 0) / 100.0) * 15.0 if ltca_data.get("is_fake") else 0.0

            # ── 6. Weighted aggregation (9 engines, total 100%) ──
            # Classic:  Spatial 28%, Temporal 15%, LTCA 15%, Noise 5%, Artifact 7%  = 70%
            # Advanced: Blink 8%, Mesh 8%, Eye Reflect 5%, LipSync 9%               = 30%
            raw_score = (
                spatial_score      * 0.28 +
                temporal_penalty   * 0.15 +
                ltca_weight        * 1.0  +   # already weighted (max 15%)
                noise_penalty      * 0.05 +
                artifact_penalty   * 0.07 +
                blink_score        * 0.08 +
                mesh_score         * 0.08 +
                reflect_score      * 0.05 +
                sync_score         * 0.09
            )

            # Multi-engine consensus harshness multiplier
            high_engines = sum([
                spatial_score > 55, temporal_penalty > 55,
                blink_score > 60, mesh_score > 55,
                sync_score > 55, noise_penalty > 60
            ])
            if high_engines >= 3:
                raw_score *= 1.20  # 3+ engines agree → apply harshness

            final_mas = float(np.clip(raw_score, 0.0, 100.0))

            # Authenticity veto — only if all major engines strongly agree video is real
            if spatial_score < 22 and temporal_penalty < 22 and blink_score < 30:
                logger.info("All 3 primary engines agree: authentic. Applying veto cap.")
                final_mas = min(final_mas, 30.0)
                if ltca_data.get("is_fake"):
                    ltca_data["is_fake"] = False
                    ltca_data["reason"] = "Vetoed by unanimous primary engines (natural video confirmed)."

            # ── 7. Attach all scores to ltca_data ──
            ltca_data["spatial_score"]     = spatial_score
            ltca_data["temporal_penalty"]  = temporal_penalty
            ltca_data["artifact_penalty"]  = artifact_penalty
            ltca_data["noise_score"]       = noise_penalty
            ltca_data["blink_score"]       = blink_score
            ltca_data["blink_detail"]      = blink_result.get("detail", "")
            ltca_data["blinks_detected"]   = blink_result.get("blinks_detected", 0)
            ltca_data["mesh_score"]        = mesh_score
            ltca_data["mesh_detail"]       = mesh_result.get("detail", "")
            ltca_data["reflect_score"]     = reflect_score
            ltca_data["reflect_detail"]    = reflect_result.get("detail", "")
            ltca_data["sync_score"]        = sync_score
            ltca_data["sync_detail"]       = sync_result.get("detail", "")
            ltca_data["sync_correlation"]  = sync_result.get("pearson_correlation", None)
            ltca_data["sync_offset"]       = sync_result.get("frame_offset", None)

            # ── 8. Build per-engine findings (feed directly into frontend KeyFindings) ──
            advanced_findings = []

            if blink_score > 0:
                advanced_findings.append({
                    "engine": "Eye-Blink-EAR",
                    "score": round(blink_score, 1),
                    "detail": blink_result.get("detail", ""),
                })
            if mesh_score > 0:
                advanced_findings.append({
                    "engine": "Face-Mesh-Tracking",
                    "score": round(mesh_score, 1),
                    "detail": mesh_result.get("detail", ""),
                })
            if reflect_score > 10:
                advanced_findings.append({
                    "engine": "Eye-Reflection-Geometry",
                    "score": round(reflect_score, 1),
                    "detail": reflect_result.get("detail", ""),
                })
            if sync_score > 0:
                advanced_findings.append({
                    "engine": "Lip-Sync-Correlation",
                    "score": round(sync_score, 1),
                    "detail": sync_result.get("detail", ""),
                })

            ltca_data["advanced_findings"] = advanced_findings

            return final_mas, ltca_data, frames

        except Exception as e:
            logger.error(f"VideoOrchestrator pipeline failed: {e}")
            import traceback; traceback.print_exc()
            return 50.0, {"nlm_report": "Forensic analysis failed due to an internal error."}, []
