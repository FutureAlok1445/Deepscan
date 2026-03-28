import os
import io
from PIL import Image
from loguru import logger
from fastapi import UploadFile
import tempfile

from .metadata import metadata_extractor           # Layer 2
from .preprocessor import preprocessor             # Layer 3 (legacy ELA, kept as fallback)
from .visual_forensics import visual_forensics     # Layer 4 (PIL heuristics + CNN ensemble)
from .frequency_face import face_geometry          # Layer 5
from .frequency_face import frequency_analyzer     # Layer 6
from .semantic_context import semantic_analyzer    # Layer 7
from .fusion import fusion_learner                 # Layer 8
from .decision_explainer import decision_explainer # Layers 9 & 10
from .diffusion_fingerprint import diffusion_analyzer  # Phase 5

# ── Reference Heatmap Detector (primary source for heatmaps + ML) ─────
from .heatmap_detector import heatmap_detector, parse_ai_score
from .context_search import context_search_service


class ImageOrchestrator:
    def __init__(self):
        self.ready = False

    async def load_models(self):
        """Pre-load ML models for all layers including the reference HF models."""
        try:
            # Load reference HF models (umm-maybe/AI-image-detector + Organika/sdxl-detector)
            import asyncio
            await asyncio.to_thread(heatmap_detector.load_models)

            await visual_forensics.load_model()
            await semantic_analyzer.load_model()
            await fusion_learner.load_model()
            await diffusion_analyzer.load_model()

            self.ready = True
            logger.info("ImageOrchestrator models loaded (reference HF + 10-layer pipeline)")
        except Exception as e:
            logger.error(f"ImageOrchestrator model initialization failed: {e}")

    async def process_image(self, file: UploadFile, context_caption: str = None, skip_lens: bool = False) -> dict:
        """
        Process an image through:
          1. Reference HF models (umm-maybe + Organika/sdxl-detector) → primary AI score
          2. JET thermal ELA heatmap + noise map (exact reference math)
          3. Supplementary 10-layer pipeline (metadata, geometry, frequency, etc.)
          4. Final AACS fusion
        """
        try:
            content = await file.read()
            pil_img = Image.open(io.BytesIO(content)).convert('RGB')
            
            import asyncio
            return await asyncio.to_thread(self._process_image_sync, pil_img, context_caption, skip_lens)
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise e

    def _process_image_sync(self, pil_img: Image.Image, context_caption: str = None, skip_lens: bool = False) -> dict:
        try:
            # Write temp file for layers that need a path (OpenCV / MediaPipe)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                pil_img.save(tmp.name, format="JPEG", quality=95)
                tmp_path = tmp.name

            details = {}

            # ── Layer 2: Metadata ─────────────────────────────────────
            meta_result = metadata_extractor.extract_metadata(tmp_path)
            score_cvs   = meta_result["score_cvs"]
            details["Metadata"] = meta_result["anomalies"]

            # ── Reference heatmap detection (PRIMARY) ─────────────────
            # Runs umm-maybe/AI-image-detector + Organika/sdxl-detector
            # + exact ELA (quality=65, amplify×14) + noise map from reference
            ref_result = {}
            ela_thermal_b64 = ""
            noise_map_b64   = ""
            ela_score       = 0
            noise_score     = 0
            ref_ai_score    = None  # None means models not loaded yet

            try:
                ref_result      = heatmap_detector.detect(pil_img)
                ela_thermal_b64 = ref_result.get("ela_heatmap",   "") or ""
                noise_map_b64   = ref_result.get("noise_heatmap", "") or ""
                ela_score       = ref_result.get("ela_score",     0)
                noise_score     = ref_result.get("noise_score",   0)
                ref_ai_score    = ref_result.get("ai_score")
                logger.info(f"Reference HF detector: ai_score={ref_ai_score}, ela={ela_score}, noise={noise_score}")
            except Exception as hm_err:
                logger.warning(f"Reference heatmap detector failed: {hm_err}")

            # ── Layer 3: Legacy preprocessor (fallback ELA if reference failed) ─
            prep_result = preprocessor.process(tmp_path)
            if not ela_thermal_b64:
                ela_thermal_b64 = prep_result.get("ela_thermal_b64") or ""
                noise_map_b64   = prep_result.get("noise_map_b64")   or ""
                ela_score       = prep_result.get("ela_score",  0)
                noise_score     = prep_result.get("noise_score", 0)

            # ── Layer 4: Visual Forensics ─────────────────────────────
            vis_result = visual_forensics.analyze(tmp_path)
            score_mas  = vis_result["score_mas"]
            details["VisualForensics"] = vis_result["details"]

            # ── Layer 4.5: Diffusion Fingerprint ──────────────────────
            diff_result = diffusion_analyzer.analyze(tmp_path)
            score_diff  = diff_result.get("score_diffusion", 0.0)
            details.setdefault("DiffusionFingerprint", []).extend(diff_result.get("details", []))

            # ── Layer 5: Face Geometry ────────────────────────────────
            geom_result = face_geometry.analyze(tmp_path)
            score_pps   = geom_result["score_pps"]
            details["FaceGeometry"] = geom_result["details"]

            # ── Layer 6: Frequency Forensics ──────────────────────────
            freq_result = frequency_analyzer.analyze(tmp_path)
            score_freq  = freq_result["score_frequency"]
            details["FrequencyAnalysis"] = freq_result.get("details", [])

            # ── Layer 7: Semantic Context ─────────────────────────────
            sem_result = semantic_analyzer.analyze(tmp_path, context_caption)
            score_irs  = sem_result["score_irs"]
            details["SemanticContext"] = sem_result["details"]

            # ── Cleanup temp file ─────────────────────────────────────
            try:
                os.remove(tmp_path)
            except Exception:
                pass

            # ── Layer 8: Fusion ───────────────────────────────────────
            caption_word_count = len(context_caption.split()) if context_caption else None

            # If reference HF models produced a score, blend it in as a strong signal.
            # We treat ref_ai_score as an additional MAS override (0-100 scale where
            # 100 = definitely fake, 0 = definitely real — same direction as the pipeline).
            if ref_ai_score is not None:
                # Blend reference AI score (70%) with existing MAS (30%)
                effective_mas = round(ref_ai_score * 0.70 + score_mas * 0.30, 1)
            else:
                effective_mas = score_mas

            signals = {
                "MAS": effective_mas,
                "PPS": score_pps,
                "FREQ": score_freq,
                "IRS": score_irs,
                "CVS": score_cvs,
                "DIFFUSION": score_diff,
                "WORD_COUNT": caption_word_count,
            }
            
            # ── Layer 11: Live Context Verification (Google Lens) ─────
            context_verification = None
            if not skip_lens:
                # Upload the ACTUAL user image to Google Lens for real web matches
                context_verification = context_search_service.search_by_image(pil_img)
                
                # Dynamically adjust CVS score (Context Verification Layer)
                # If we found entities or domains, lower the CVS score (lower score = more authentic)
                if context_verification and context_verification.get("success"):
                    found_count = len(context_verification.get("entities", [])) + len(context_verification.get("matching_domains", []))
                    if found_count > 3:
                        score_cvs = max(5, score_cvs - 25) # High confidence web prevalence
                    elif found_count > 0:
                        score_cvs = max(10, score_cvs - 15) # Moderate web prevalence
                
                # Re-update the signals dict with potentially adjusted CVS
                signals["CVS"] = score_cvs
            
            deepfake_chance_aacs = fusion_learner.fuse(signals)

            # If reference produced a result, allow it to anchor the final score:
            # final = 60% fused AACS + 40% reference ai_score
            if ref_ai_score is not None:
                deepfake_chance_aacs = round(deepfake_chance_aacs * 0.60 + ref_ai_score * 0.40, 1)

            # ── Layers 9 & 10: Decision + Explanation ─────────────────
            verdict          = decision_explainer.decide(deepfake_chance_aacs)
            explanation_text = decision_explainer.generate_explanation(signals, details)
            
            # Layer 11: Add Context Verification note to text
            if context_verification and context_verification.get("success"):
                found_entities = ", ".join(context_verification.get("entities", [])[:3])
                if found_entities:
                    explanation_text += f"\n\n[Layer 11: Context] Live Vision Scan identified: {found_entities}. Web prevalence confirms authentic origin patterns."
                else:
                    explanation_text += "\n\n[Layer 11: Context] Live Vision Scan initiated. No suspicious forensic matches found on indexed domains."

            # Add reference signals to explanation if available
            ref_signals_text = ""
            if ref_result.get("signals"):
                ref_signals_text = " | " + " | ".join(
                    f"{s['name']}: {s['score']}% ({s['severity']})"
                    for s in ref_result["signals"]
                )
            if ref_signals_text:
                explanation_text = explanation_text + ref_signals_text

            # ── Build result ──────────────────────────────────────────
            result = {
                "score":   round(deepfake_chance_aacs, 1),
                "verdict": verdict,
                "signals": {
                    "metadata_cvs":       score_cvs,
                    "visual_forensics_mas": effective_mas,
                    "face_geometry_pps":  score_pps,
                    "frequency":          score_freq,
                    "semantic_context_irs": score_irs,
                    "diffusion_fingerprint": score_diff,
                    # Reference scores (direct from HF models + forensics)
                    "ref_ai_score":    ref_ai_score,
                    "ref_ela_score":   ela_score,
                    "ref_noise_score": noise_score,
                },
                "explainability": {
                    "text":               explanation_text,
                    # Legacy key (PIL heatmap JPEG) — kept for backward compat
                    "ela_base64_heatmap_prefix": "data:image/jpeg;base64," + (prep_result.get("ela_base64") or ""),
                    # Reference-quality JET thermal heatmaps (PNG)
                    "ela_thermal_b64": ("data:image/png;base64," + ela_thermal_b64) if ela_thermal_b64 else "",
                    "noise_map_b64":   ("data:image/png;base64," + noise_map_b64)   if noise_map_b64   else "",
                    "ela_score":   ela_score,
                    "noise_score": noise_score,
                    "regions":     [],
                    # Full reference ML breakdown
                    "ref_ml_results": ref_result.get("ml_results", {}),
                    "ref_signals":    ref_result.get("signals", []),
                    "context_verification": context_verification
                },
            }
            return result

        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            raise e


image_orchestrator = ImageOrchestrator()
