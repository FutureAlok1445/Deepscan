import os
import asyncio
from loguru import logger
from backend.utils.hf_api import query_huggingface
from backend.services.detection.image_forensics import ELAAnalyzer, ImageNoiseAnalyzer
from backend.services.detection.face_xray import FaceXRayAnalyzer

class ImageDetector:
    def __init__(self):
        self.model_id = "prithivMLmods/Deep-Fake-Detector-v2-Model"
        self.ela = ELAAnalyzer()
        self.noise = ImageNoiseAnalyzer()
        self.face_xray = FaceXRayAnalyzer()
        logger.info(f"ImageDetector initialized with HF model & 3 Local Forensic Engines")

    def predict(self, image_path: str) -> float:
        """
        Synchronous wrapper for predict_async to maintain compatibility 
        with existing orchestrator signature if needed, though orchestrator 
        is async-capable.
        """
        return asyncio.run(self.predict_async(image_path))

    async def predict_async(self, image_path: str) -> tuple[float, list]:
        """
        Detects if an image is a deepfake using a 4-engine pipeline:
        1. Vision Transformer (ViT)
        2. Error Level Analysis (ELA)
        3. Noise Variance (PRNU isolation)
        4. Face X-Ray (Splicing Blending Boundaries)
        Returns a consensus score (0-100) and detailed findings.
        """
        try:
            vit_score = 50.0
            vit_detail = "HuggingFace API unavailable or error"
            
            # Start local forensic tasks
            loop = asyncio.get_event_loop()
            ela_task = loop.run_in_executor(None, self.ela.analyze, image_path)
            noise_task = loop.run_in_executor(None, self.noise.analyze, image_path)
            xray_task = loop.run_in_executor(None, self.face_xray.analyze, image_path)

            # Query HF API
            try:
                result = await query_huggingface(self.model_id, file_path=image_path)
                if not "error" in result:
                    if isinstance(result, list):
                        for item in result:
                            label = str(item.get("label", "")).lower()
                            if label in ["fake", "deepfake", "label_1", "synthetic"]:
                                vit_score = item.get("score", 0.0) * 100
                                break
                            if label == "deepfake":
                                vit_score = item.get("score", 0.0) * 100
                                break
                        if vit_score == 50.0 or vit_score == 0.0:  # If we only saw "Real"
                            for item in result:
                                label = str(item.get("label", "")).lower()
                                if label in ["real", "authentic", "label_0", "realism"]:
                                    vit_score = (1.0 - item.get("score", 1.0)) * 100
                                    break
                    vit_detail = "HuggingFace ViT spatial manipulation detection"
            except Exception as e:
                logger.error(f"HF Image query failed: {e}")

            # Await local tasks
            ela_res, noise_res, xray_res = await asyncio.gather(ela_task, noise_task, xray_task)

            img_findings = [
                {
                    "engine": "Vision-Transformer-ViT", 
                    "score": round(vit_score, 1), 
                    "detail": vit_detail,
                    "reasoning": "Spatial feature analysis via a pre-trained Vision Transformer (ViT) model, matching global manipulation patterns against a known deepfake manifold."
                },
                {
                    "engine": "Face-XRay-Blend-Boundary", 
                    "score": round(xray_res["score"], 1), 
                    "detail": xray_res["detail"],
                    "reasoning": xray_res.get("reasoning", "")
                },
                {
                    "engine": "Error-Level-Analysis", 
                    "score": round(ela_res["score"], 1), 
                    "detail": ela_res["detail"],
                    "reasoning": ela_res.get("reasoning", "")
                },
                {
                    "engine": "High-Freq-Noise-PRNU", 
                    "score": round(noise_res["score"], 1), 
                    "detail": noise_res["detail"],
                    "reasoning": noise_res.get("reasoning", "")
                },
            ]

            # Consensus scoring (ViT 55%, X-Ray 15%, ELA 15%, Noise 15%)
            final_score = (vit_score * 0.55) + (xray_res["score"] * 0.15) + (ela_res["score"] * 0.15) + (noise_res["score"] * 0.15)
            
            # Harshness veto (if 2+ engines agree the image is highly synthetic)
            high_engines = sum([vit_score > 70, ela_res["score"] > 70, noise_res["score"] > 70, xray_res["score"] > 70])
            if high_engines >= 2:
                final_score *= 1.15

            return min(final_score, 100.0), img_findings

        except Exception as e:
            logger.error(f"ImageDetector pipeline failed: {e}")
            return 50.0, []