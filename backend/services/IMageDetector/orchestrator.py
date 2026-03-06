import os
import io
from PIL import Image
from loguru import logger
from fastapi import UploadFile
import tempfile

from .metadata import metadata_extractor           # Layer 2
from .preprocessor import preprocessor             # Layer 3
from .visual_forensics import visual_forensics     # Layer 4 (PIL heuristics + CNN ensemble)
from .frequency_face import face_geometry          # Layer 5 (PIL symmetry/skin-tone heuristics)
from .frequency_face import frequency_analyzer     # Layer 6 (PIL frequency heuristics + FFT)
from .semantic_context import semantic_analyzer    # Layer 7
from .fusion import fusion_learner                 # Layer 8
from .decision_explainer import decision_explainer # Layers 9 & 10
from .claude_vision import claude_analyzer         # Phase 4
from .diffusion_fingerprint import diffusion_analyzer # Phase 5

class ImageOrchestrator:
    def __init__(self):
        self.ready = False

    async def load_models(self):
        """Pre-load ML models for the 10 layers."""
        try:
            await visual_forensics.load_model()
            await semantic_analyzer.load_model()
            await fusion_learner.load_model()
            await claude_analyzer.load_model()
            await diffusion_analyzer.load_model()
            
            self.ready = True
            logger.info("ImageOrchestrator 10-Layer models loaded successfully")
        except Exception as e:
            logger.error(f"ImageOrchestrator model initialization failed: {e}")

    async def process_image(self, file: UploadFile, context_caption: str = None) -> dict:
        """Process an image through the 10-layer forensic architecture."""
        try:
            # Setup temp file for ML layers that require path (e.g. MediaPipe, OpenCV)
            content = await file.read()
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                img = Image.open(io.BytesIO(content)).convert('RGB')
                img.save(tmp.name, format="JPEG")
                tmp_path = tmp.name

            details = {}
                
            # Layer 2: Metadata
            meta_result = metadata_extractor.extract_metadata(tmp_path)
            score_cvs = meta_result["score_cvs"]
            details["Metadata"] = meta_result["anomalies"]
            
            # Layer 3: Preprocessing
            prep_result = preprocessor.process(tmp_path)
            
            # Layer 4: Visual Forensics
            vis_result = visual_forensics.analyze(tmp_path)
            score_mas = vis_result["score_mas"]
            details["VisualForensics"] = vis_result["details"]
            
            # Layer 4.5: Diffusion Noise Fingerprint (Phase 5)
            diff_result = diffusion_analyzer.analyze(tmp_path)
            score_diff = diff_result.get("score_diffusion", 0.0)
            details.setdefault("DiffusionFingerprint", []).extend(diff_result.get("details", []))

            # Layer 5: Face Geometry
            geom_result = face_geometry.analyze(tmp_path)
            score_pps = geom_result["score_pps"]
            details["FaceGeometry"] = geom_result["details"]
            
            # Layer 6: Frequency Forensics
            freq_result = frequency_analyzer.analyze(tmp_path)
            score_freq = freq_result["score_frequency"]
            details["FrequencyAnalysis"] = freq_result.get("details", [])
            
            # Layer 7: Semantic Context
            sem_result = semantic_analyzer.analyze(tmp_path, context_caption)
            score_irs = sem_result["score_irs"]
            details["SemanticContext"] = sem_result["details"]

            # Phase 4: High-Fidelity Heatmaps (Claude Vision)
            base64_img = prep_result.get("base64")
            if base64_img:
                import mimetypes
                mime_type = mimetypes.guess_type(tmp_path)[0] or "image/jpeg"
                claude_result = claude_analyzer.analyze(base64_img, mime_type)
                regions = claude_result.get("regions", [])
                
                # Optionally append claude signals to details if needed
                for sig in claude_result.get("signals", []):
                    if sig.get("status") in ["detected", "warning"]:
                        details.setdefault("ClaudeVision", []).append(f"{sig['label']}: {sig['detail']}")
            else:
                regions = []

            # Layer 8: Fusion
            # NOTE: WORD_COUNT is passed to apply BBC-dataset-derived word-length correction.
            # BBC finding: short content (<400 words) has 38% higher AI probability than long-form.
            caption_word_count = len(context_caption.split()) if context_caption else None
            signals = {
                "MAS": score_mas, "PPS": score_pps,
                "FREQ": score_freq, "IRS": score_irs, "CVS": score_cvs,
                "DIFFUSION": score_diff,
                "WORD_COUNT": caption_word_count
            }
            deepfake_chance_aacs = fusion_learner.fuse(signals)

            # Layer 9 & 10: Explainability and Decision
            verdict = decision_explainer.decide(deepfake_chance_aacs)
            explanation_text = decision_explainer.generate_explanation(signals, details)

            # Cleanup
            os.remove(tmp_path)
            
            result = {
                "score": round(deepfake_chance_aacs, 1),
                "verdict": verdict,
                "signals": {
                    "metadata_cvs": score_cvs,
                    "visual_forensics_mas": score_mas,
                    "face_geometry_pps": score_pps,
                    "frequency": score_freq,
                    "semantic_context_irs": score_irs,
                    "diffusion_fingerprint": score_diff
                },
                "explainability": {
                    "text": explanation_text,
                    "ela_base64_heatmap_prefix": "data:image/jpeg;base64," + (prep_result.get("ela_base64") or ""),
                    "regions": regions
                }
            }
            return result
            
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise e

image_orchestrator = ImageOrchestrator()
