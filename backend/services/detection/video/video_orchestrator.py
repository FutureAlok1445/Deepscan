import os
import cv2
import numpy as np
import asyncio
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
from backend.services.detection.video.video_describer import VideoDescriber
from backend.services.detection.video.biological_analyzer import BiologicalAnalyzer
from backend.services.explainability.video_nlm_report import VideoNLMReport
from .sota_models import sota_ensemble, ensemble_sota

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
        self.rppg = BiologicalAnalyzer()
        self.describer = VideoDescriber()
        self.nlm_reporter = VideoNLMReport()
        logger.info("VideoOrchestrator loaded — 10 detection engines + VideoDescriber active")

    async def process_video(self, video_path: str, num_frames=16) -> tuple:
        """
        Full-spectrum video detection pipeline.
        Engines:
          Classic:  LTCA (Physics), Spatial (ViT), Temporal (Optical Flow), Noise (FFT+Wavelet+PRNU), Artifact (DCT+Residue)
          Advanced: Eye Blink (EAR), Face Mesh (LK), Eye Reflection, Lip-Sync (AV Cross-Corr)
        """
        try:
            # ── 2. Frame Extraction (Optimized: One pass) ──
            # Increasing num_frames for much higher accuracy in Biological/LipSync/Mesh
            target_frames = 80 
            cap = cv2.VideoCapture(video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30.0

            if total <= 1:
                logger.warning(f"VideoOrchestrator aborted: fewer than 2 frames in {video_path}")
                cap.release()
                return 50.0, {
                    "nlm_report": "Deepscan aborted: The video contains fewer than 2 readable frames. Try re-encoding as H.264 MP4."
                }, []

            # Sample frames evenly
            frame_indices = np.linspace(0, total - 1, target_frames, dtype=int)
            frames = []
            for idx in frame_indices:
                cap.set(cv2.CAP_PROP_POS_FRAMES, idx)
                ret, frame = cap.read()
                if ret:
                    # Optional: minor downscale here if files are 4K to save RAM
                    if frame.shape[1] > 1280:
                        frame = cv2.resize(frame, (1280, 720))
                    frames.append(frame)
            cap.release()

            if len(frames) < 10:
                return 50.0, {"nlm_report": "Analysis failed: Not enough frames could be decoded."}, []

            # ── 3. Optimized AI/Forensic Engine Execution (Concurrent) ──
            # passing the SAME frame pool to all engines to avoid redundant reads
            
            # Physics (LTCA) - Now uses the decoded frames list directly
            ltca_task = asyncio.create_task(asyncio.to_thread(self.ltca.analyze_trajectory, frames))
            
            # Classic Spatial/Temporal/Noise/Artifact
            spatial_task = asyncio.create_task(self.spatial.analyze_frames([frames[0], frames[len(frames)//2], frames[-1]]))
            temporal_task = asyncio.to_thread(self.temporal.analyze_sequence, frames)
            noise_task = asyncio.to_thread(self.noise.analyze_frames, frames)
            artifact_task = asyncio.to_thread(self.artifact_scanner.analyze_frames, frames)

            # Advanced Biological/Tracking/LipSync
            blink_task   = asyncio.to_thread(self.blink.analyze_frames, frames, fps)
            mesh_task    = asyncio.to_thread(self.face_mesh.analyze_frames, frames)
            reflect_task = asyncio.to_thread(self.eye_reflection.analyze_frames, frames)
            sync_task    = self.lip_sync.analyze(video_path, frames)
            rppg_task    = asyncio.to_thread(self.rppg.analyze_frames, frames, fps)

            # SOTA CNN tasks
            meso_task = asyncio.to_thread(lambda: sota_ensemble['mesonet4'].predict(frames[0]))
            xcep_task = asyncio.to_thread(lambda: sota_ensemble['xception'].predict(frames[len(frames)//2]))

            # ── Qwen3 VL forensic description — launched NOW as concurrent task ──
            # IMPORTANT: Must be created as asyncio.Task() BEFORE gather so it
            # runs concurrently with the detection engines, not sequentially after.
            filename = os.path.basename(video_path)
            logger.info(f"[Qwen3 VL] Sending {min(8, len(frames))} frames to LM Studio for forensic description...")
            description_task = asyncio.ensure_future(self.describer.describe(frames, filename=filename))

            # Gather ALL 10 engines (Qwen runs concurrently in background)
            (
                ltca_data,
                spatial_score, temporal_penalty, noise_penalty, artifact_penalty,
                blink_result, mesh_result, reflect_result, sync_result, rppg_result
            ) = await asyncio.gather(
                ltca_task,
                spatial_task, temporal_task, noise_task, artifact_task,
                blink_task, mesh_task, reflect_task, sync_task, rppg_task
            )

            blink_score   = blink_result.get("score", 50.0)
            mesh_score    = mesh_result.get("score", 50.0)
            reflect_score = reflect_result.get("score", 50.0)
            sync_score    = sync_result.get("score", 50.0)
            rppg_score    = rppg_result.get("score", 50.0)

            # ── 4. Weighted aggregation (LTCA 15%, etc.) ──
            ltca_weight = (ltca_data.get("confidence", 0) / 100.0) * 15.0 if ltca_data.get("is_fake") else 0.0

            raw_score = (
                spatial_score      * 0.25 +
                temporal_penalty   * 0.15 +
                ltca_weight        * 1.0  +  
                noise_penalty      * 0.05 +
                artifact_penalty   * 0.05 +
                blink_score        * 0.08 +
                mesh_score         * 0.08 +
                reflect_score      * 0.05 +
                sync_score         * 0.08 +
                rppg_score         * 0.06
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
            ltca_data["rppg_bpm"]          = rppg_result.get("heart_rate_bpm", None)
            ltca_data["rppg_snr"]          = rppg_result.get("snr", None)

            # ── 8. Build per-engine findings (feed directly into frontend KeyFindings) ──
            advanced_findings = []

            if blink_score > 0:
                advanced_findings.append({
                    "engine": "Eye-Blink-EAR",
                    "score": round(blink_score, 1),
                    "detail": blink_result.get("detail", ""),
                    "reasoning": blink_result.get("reasoning", "")
                })
            if mesh_score > 0:
                advanced_findings.append({
                    "engine": "Face-Mesh-Tracking",
                    "score": round(mesh_score, 1),
                    "detail": mesh_result.get("detail", ""),
                    "reasoning": mesh_result.get("reasoning", "")
                })
            if reflect_score > 10:
                advanced_findings.append({
                    "engine": "Eye-Reflection-Geometry",
                    "score": round(reflect_score, 1),
                    "detail": reflect_result.get("detail", ""),
                    "reasoning": reflect_result.get("reasoning", "Specular highlight geometry analysis to detect inconsistent light-source reflection in eye corneas.")
                })
            if sync_score > 0:
                advanced_findings.append({
                    "engine": "Lip-Sync-Correlation",
                    "score": round(sync_score, 1),
                    "detail": sync_result.get("detail", ""),
                    "reasoning": sync_result.get("reasoning", "")
                })
            
            # Add rPPG findings so it surfaces on the frontend
            if rppg_score > 0:
                advanced_findings.append({
                    "engine": "rPPG-Biological-Pulse",
                    "score": round(rppg_score, 1),
                    "detail": rppg_result.get("detail", ""),
                    "reasoning": rppg_result.get("reasoning", "")
                })

            ltca_data["advanced_findings"] = advanced_findings

            # ── 9. Await content description (runs concurrently with scoring) ──
            try:
                video_description = await description_task
                ltca_data["video_description"] = video_description
            except Exception as desc_err:
                logger.warning(f"VideoDescriber task failed: {desc_err}")
                ltca_data["video_description"] = {"description": "Content analysis unavailable.", "moments": []}

            return final_mas, ltca_data, frames

        except Exception as e:
            logger.error(f"VideoOrchestrator pipeline failed: {e}")
            import traceback; traceback.print_exc()
            return 50.0, {"nlm_report": "Forensic analysis failed due to an internal error."}, []
