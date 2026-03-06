import os
import asyncio
import uuid
import time
import traceback
from loguru import logger

from backend.services.detection.image_detector import ImageDetector
from backend.services.detection.video.video_orchestrator import VideoOrchestrator
from backend.services.detection.audio_detector import AudioDetector
from backend.services.detection.text_detector import TextDetector
from backend.services.physiological.rppg_detector import RPPGDetector
from backend.services.forensics.ela_analysis import run_ela
from backend.services.forensics.fft_analysis import FFTAnalyzer
from backend.services.forensics.noise_analysis import NoiseAnalyzer
from backend.services.forensics.metadata_extractor import MetadataExtractor
from backend.services.forensics.gabor_filter import build_filters, process as gabor_process
from backend.services.fusion.cdcf_engine import CDCFEngine
from backend.services.fusion.score_calculator import calculate_aacs, get_verdict
from backend.services.context.news_cross_checker import NewsCrossChecker
from backend.services.context.reverse_image_search import ReverseImageSearch
from backend.services.context.semantic_analyzer import SemanticAnalyzer
from backend.services.explainability.llm_narrator import narrate


class DetectionOrchestrator:
    """Central orchestrator that wires together all detection engines,
    forensic analysers, physiological validators, context verifiers,
    CDCF fusion, and explainability modules to produce the full
    AACS (AI Authenticity Confidence Score) result."""

    def __init__(self):
        self.models_loaded = False
        # Detection engines
        self.image_detector = None
        self.video_detector = None
        self.audio_detector = None
        self.text_detector = None
        # Physiological
        self.rppg_detector = None
        # Forensics
        self.fft_analyzer = None
        self.noise_analyzer = None
        self.metadata_extractor = None
        # Fusion
        self.cdcf_engine = None
        # Context
        self.news_checker = None
        self.reverse_search = None
        self.semantic_analyzer = None

    async def load_models(self):
        """Lazy-load all ML models and service instances."""
        if self.models_loaded:
            return True
        logger.info("Loading ML models for Orchestrator...")
        try:
            self.image_detector = ImageDetector()
            self.video_detector = VideoOrchestrator()
            self.audio_detector = AudioDetector()
            self.text_detector = TextDetector()
            self.rppg_detector = RPPGDetector()
            self.fft_analyzer = FFTAnalyzer()
            self.noise_analyzer = NoiseAnalyzer()
            self.metadata_extractor = MetadataExtractor()
            self.cdcf_engine = CDCFEngine()
            self.news_checker = NewsCrossChecker()
            self.reverse_search = ReverseImageSearch()
            self.semantic_analyzer = SemanticAnalyzer()
            self.models_loaded = True
            logger.info("All models loaded successfully.")
            return True
        except Exception as e:
            logger.error(f"Model loading failed: {e}")
            return False

    # ------------------------------------------------------------------ helpers
    def _detect_file_category(self, file_path: str, file_type: str) -> str:
        """Return 'image', 'video', 'audio', or 'unknown'."""
        ext = os.path.splitext(file_path)[1].lower()
        ft = file_type.lower() if file_type else ""
        if ext in (".jpg", ".jpeg", ".png", ".bmp", ".webp") or "image" in ft:
            return "image"
        if ext in (".mp4", ".avi", ".mov", ".mkv", ".webm") or "video" in ft:
            return "video"
        if ext in (".wav", ".mp3", ".m4a", ".flac", ".ogg") or "audio" in ft:
            return "audio"
        return "unknown"

    # ------------------------------------------------------------------ MAS
    async def _compute_mas(self, file_path: str, category: str) -> tuple:
        """Media Authenticity Score — primary deepfake detection."""
        findings = []
        ltca_data = {}
        try:
            if category == "image":
                score = await self.image_detector.predict_async(file_path)
                findings.append({"engine": "Vision-Transformer-ViT", "score": round(score, 1),
                                 "detail": "HuggingFace-backed spatial manipulation detection"})
            elif category == "video":
                # Run 9-engine VideoOrchestrator (returns score, ltca_data, frames)
                score, ltca_data, frames = await self.video_detector.process_video(file_path, num_frames=16)
                ltca_data["frames"] = frames  # kept for internal semantic analysis, stripped before HTTP response

                findings.append({
                    "engine": "Spatio-Temporal-Analysis",
                    "score": round(score, 1),
                    "detail": "9-engine pipeline: ViT + Optical Flow + LTCA + DCT Artifact + Wavelet Noise + Blink + Face Mesh + Eye Reflection + Lip-Sync"
                })

                if ltca_data and ltca_data.get("is_fake"):
                    findings.append({
                        "engine": "Latent-Trajectory-Curvature",
                        "score": round(ltca_data.get("confidence", 0), 1),
                        "detail": ltca_data.get("reason", "Physics Violation Detected")
                    })

                # Merge per-engine advanced findings (Blink, Mesh, Reflect, LipSync)
                for af in ltca_data.get("advanced_findings", []):
                    findings.append(af)

                self._last_ltca_data = ltca_data

            elif category == "audio":
                score = await self.audio_detector.analyze(file_path)
                findings.append({"engine": "Audio-Spoof-Detection", "score": round(score, 1),
                                 "detail": "AI Voice Clone / Synthetic Speech analysis"})
            else:
                score = 50.0
                ltca_data = {}
        except Exception as e:
            logger.warning(f"MAS computation error: {e}")
            score = 50.0
            ltca_data = {}
        return round(score, 2), findings, ltca_data

    # ------------------------------------------------------------------ PPS
    async def _compute_pps(self, file_path: str, category: str) -> tuple:
        """Physiological Plausibility Score — rPPG heartbeat analysis."""
        findings = []
        if category != "video":
            return 0.0, [{"engine": "rPPG", "score": 0.0, "detail": "Skipped — not a video file"}]
        try:
            rppg = self.rppg_detector.process_video(file_path)
            score = rppg.get("deepfake_prob", 50.0)
            hr = rppg.get("heart_rate", 0)
            conf = rppg.get("confidence", 0)
            findings.append({
                "engine": "rPPG-Heartbeat", "score": round(score, 1),
                "detail": f"Detected HR: {hr:.0f} BPM, confidence: {conf:.0%}",
                "heart_rate": hr, "confidence": conf,
                "signal": rppg.get("signal", []),
            })
            return round(score, 2), findings
        except Exception as e:
            logger.warning(f"PPS computation error: {e}")
            return 50.0, [{"engine": "rPPG", "score": 50.0, "detail": str(e)}]

    # ------------------------------------------------------------------ IRS
    async def _compute_irs(self, file_path: str, category: str) -> tuple:
        """Information Reliability Score — text/context verification."""
        findings = []
        # Metadata check (using improved extractor with Pillow fallback)
        meta = self.metadata_extractor.extract(file_path)
        meta_score = 0.0
        suspicious_keys = ["Adobe Photoshop", "GIMP", "FaceApp", "DeepFaceLab", "Midjourney", "DALL-E", "Stable Diffusion"]
        
        # Check software/comments for known AI strings
        software = str(meta.get("Software", "")).lower()
        if any(s.lower() in software for s in suspicious_keys):
            meta_score = 75.0
            findings.append({"engine": "MetadataCheck", "score": 75.0,
                             "detail": f"AI Generation Software detected: {meta.get('Software')}"})
        else:
            findings.append({"engine": "MetadataCheck", "score": 0.0,
                             "detail": "No suspicious metadata/software signatures found"})
        
        # News cross-check
        news_ok = self.news_checker.verify_event(f"file:{file_path}")
        if not news_ok:
            meta_score = max(meta_score, 40.0)
            findings.append({"engine": "NewsCrossCheck", "score": 40.0,
                             "detail": "No matching credible news source found for the event context"})
        return round(meta_score, 2), findings

    # ------------------------------------------------------------------ AAS
    async def _compute_aas(self, file_path: str, category: str) -> tuple:
        """Acoustic Anomaly Score — audio deepfake clues."""
        findings = []
        if category not in ("audio", "video"):
            return 0.0, [{"engine": "AudioAnalysis", "score": 0.0, "detail": "Skipped — no audio track"}]
        try:
            score = await self.audio_detector.analyze(file_path)
            findings.append({"engine": "AI-Audio-Scanner", "score": round(score, 1),
                             "detail": "Transformer-based voice cloning analysis"})
            return round(score, 2), findings
        except Exception as e:
            return 50.0, [{"engine": "AudioAnalysis", "score": 50.0, "detail": str(e)}]

    # ------------------------------------------------------------------ CVS
    async def _compute_cvs(self, file_path: str, category: str) -> tuple:
        """Contextual Verification Score — reverse image search + provenance."""
        findings = []
        try:
            rev = self.reverse_search.search(file_path)
            penalty = rev.get("trust_penalty", 0.0)
            matches = rev.get("matches_found", 0)
            if matches > 0:
                findings.append({"engine": "ReverseImageSearch", "score": round(penalty, 1),
                                 "detail": f"Found {matches} visual matches online"})
            else:
                findings.append({"engine": "ReverseImageSearch", "score": 0.0,
                                 "detail": "No duplicate/source images found"})
            return round(penalty, 2), findings
        except Exception as e:
            return 0.0, [{"engine": "ContextSearch", "score": 0.0, "detail": str(e)}]

    # ------------------------------------------------------------------ Forensics
    async def _run_forensics(self, file_path: str, category: str) -> dict:
        """ELA, FFT, Noise analysis for images/video frames."""
        forensics = {"ela": None, "fft": None, "noise": None, "metadata": {}}
        if category not in ("image", "video"):
            return forensics
        target = file_path
        # For video, extract a key frame
        if category == "video":
            try:
                import cv2
                cap = cv2.VideoCapture(file_path)
                total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
                cap.set(cv2.CAP_PROP_POS_FRAMES, total // 2)
                ret, frame = cap.read()
                cap.release()
                if ret:
                    import tempfile as _tf
                    target = os.path.join(_tf.gettempdir(), f"deepscan_forensic_{uuid.uuid4().hex}.jpg")
                    cv2.imwrite(target, frame)
            except Exception:
                pass
        try:
            forensics["ela"] = run_ela(target)
        except Exception as e:
            logger.warning(f"ELA failed: {e}")
        try:
            forensics["fft"] = self.fft_analyzer.analyze(target)
        except Exception as e:
            logger.warning(f"FFT failed: {e}")
        try:
            forensics["noise"] = {"noise_score": self.noise_analyzer.evaluate(target)}
        except Exception as e:
            logger.warning(f"Noise failed: {e}")
        try:
            forensics["metadata"] = self.metadata_extractor.extract(file_path)
        except Exception:
            pass
        return forensics

    # ------------------------------------------------------------------ main pipeline
    async def process_media(self, file_path: str, file_type: str) -> dict:
        """Run the full AACS pipeline and return a complete result dict
        that matches the frontend's expected data shape."""
        start = time.time()
        analysis_id = f"ds-{uuid.uuid4().hex[:12]}"
        category = self._detect_file_category(file_path, file_type)
        logger.info(f"[{analysis_id}] Starting AACS pipeline — category={category}")

        if not self.models_loaded:
            await self.load_models()

        all_findings = []

        # ---------- Compute 5 sub-scores in parallel ----------
        # Run sub-scores concurrently
        ltca_data_payload = {}
        try:
            # We run MAS (detector) and other sub-scores
            (mas, mas_f, ltca_data_payload), (pps, pps_f), (irs, irs_f), (aas, aas_f), (cvs, cvs_f) = await asyncio.gather(
                self._compute_mas(file_path, category),
                self._compute_pps(file_path, category),
                self._compute_irs(file_path, category),
                self._compute_aas(file_path, category),
                self._compute_cvs(file_path, category),
            )
            # EXTRA: Semantic Fact-Checking (Vision LLM + Fact Check API)
            if category == "video" and ltca_data_payload.get("frames"):
                frames = ltca_data_payload.get("frames")
                try:
                    semantic = await self.semantic_analyzer.describe_and_verify(frames)
                    ltca_data_payload["semantic_analysis"] = semantic
                    
                    # Cross-check claims with Fact Check tools
                    for claim in semantic.get("claims", []):
                        verification = await self.news_checker.verify_with_api(claim)
                        if verification.get("found"):
                            rating = verification.get("first_rating", "Unknown").lower()
                            if any(p in rating for p in ["false", "misleading", "fake", "manipulated"]):
                                cvs_f.append({"engine": "Semantic-Fact-Check", "score": 98.0, 
                                              "detail": f"DEEPFAKE CONTEXT: Claim '{claim}' flagged as {rating.upper()} by independent sources."})
                                cvs = max(cvs, 98.0)
                            elif any(p in rating for p in ["true", "correct", "accurate"]):
                                cvs_f.append({"engine": "Semantic-Fact-Check", "score": 0.0, 
                                              "detail": f"VERIFIED CONTEXT: Scene content corroborated as {rating.upper()}."})
                except Exception as semantic_err:
                    logger.warning(f"Semantic checking failed: {semantic_err}")

        except Exception as e:
            logger.error(f"Sub-score computation failed: {e}\n{traceback.format_exc()}")
            mas = pps = irs = aas = cvs = 50.0
            mas_f = pps_f = irs_f = aas_f = cvs_f = []

        all_findings.extend(mas_f + pps_f + irs_f + aas_f + cvs_f)

        # ---------- CDCF Fusion ----------
        scores_dict = {"mas": mas, "pps": pps, "irs": irs, "aas": aas, "cvs": cvs}
        fusion = self.cdcf_engine.fuse(scores_dict)
        aacs_score = fusion["aacs"]
        verdict = fusion["verdict"]

        # ---------- Forensics (non-blocking) ----------
        forensics = await self._run_forensics(file_path, category)

        # ---------- Build response matching frontend shape ----------
        # Extract heartbeat data from PPS findings if available
        heartbeat_data = {}
        for f in pps_f:
            if f.get("engine") == "rPPG-Heartbeat":
                heartbeat_data = {
                    "heart_rate": f.get("heart_rate", 0),
                    "confidence": f.get("confidence", 0),
                    "signal": f.get("signal", []),
                }
                break

        # ---------- NLM Forensic Report (Video Only) ----------
        if category == "video":
            from backend.services.explainability.video_nlm_report import VideoNLMReport
            nlm_reporter = VideoNLMReport()
            try:
                # We now have access to both physics (ltca) AND biology (rppg) data here
                nlm_text = await nlm_reporter.generate_report(
                    mas_score=aacs_score,
                    spatial_score=ltca_data_payload.get("spatial_score", 50.0),
                    temporal_penalty=ltca_data_payload.get("temporal_penalty", 50.0),
                    noise_score=ltca_data_payload.get("noise_score", 50.0),
                    artifact_penalty=ltca_data_payload.get("artifact_penalty", 50.0),
                    ltca_data=ltca_data_payload,
                    rppg_data=heartbeat_data
                )
                ltca_data_payload["nlm_report"] = nlm_text
            except Exception as e:
                logger.error(f"Failed to generate Video NLM report: {e}")
                ltca_data_payload["nlm_report"] = "Forensic NLM analysis failed due to system error."

        # ---------- LLM Narration (best-effort) ----------
        narrative = {"summary": "", "eli5": "", "detailed": "", "technical": ""}
        try:
            summary_text = await narrate(aacs_score, [f.get("detail", "") for f in all_findings[:5]])
            narrative["summary"] = summary_text
            narrative["eli5"] = summary_text
            narrative["detailed"] = f"AACS Score: {aacs_score:.1f} — {verdict}. {summary_text}"
            narrative["technical"] = (
                f"Sub-scores: MAS={mas:.1f} PPS={pps:.1f} IRS={irs:.1f} AAS={aas:.1f} CVS={cvs:.1f}. "
                f"CDCF multiplier: {fusion['multiplier']:.2f}x. "
                f"Contradictions: {len(fusion['contradictions'])}. Final AACS: {aacs_score:.1f}."
            )
        except Exception as e:
            logger.warning(f"Narration failed: {e}")
            narrative["summary"] = f"AACS Score: {aacs_score:.1f} — {verdict}"

        elapsed = round(time.time() - start, 2)
        logger.info(f"[{analysis_id}] Pipeline complete in {elapsed}s — AACS={aacs_score:.1f} ({verdict})")

        # ---------- Build response matching frontend shape ----------
        # Extract heartbeat data from PPS findings if available
        heartbeat_data = {}
        for f in pps_f:
            if f.get("engine") == "rPPG-Heartbeat":
                heartbeat_data = {
                    "heart_rate": f.get("heart_rate", 0),
                    "confidence": f.get("confidence", 0),
                    "signal": f.get("signal", []),
                }
                break

        # Strip non-JSON-serializable objects before building the response
        # (Raw video frames are NumPy arrays — they cannot be JSON encoded)
        ltca_data_payload.pop("frames", None)

        return {
            "id": analysis_id,
            "filename": os.path.basename(file_path),
            "file_type": category,
            "status": "complete",
            "score": round(aacs_score, 1),
            "aacs_score": round(aacs_score, 1),
            "verdict": verdict,
            "verdict_color": fusion["verdict_color"],
            "sub_scores": {
                "mas": round(mas, 1),
                "pps": round(pps, 1),
                "irs": round(irs, 1),
                "aas": round(aas, 1),
                "cvs": round(cvs, 1),
            },
            "fusion": {
                "contradictions": fusion["contradictions"],
                "multiplier": fusion["multiplier"],
                "confidence_note": fusion["confidence_note"],
            },
            "cdcf": {
                "contradictions": fusion["contradictions"],
                "multiplier": fusion["multiplier"],
                "confidence_note": fusion["confidence_note"],
                "consensus": max(0, 100 - len(fusion["contradictions"]) * 10),
                "dissent": min(100, len(fusion["contradictions"]) * 10),
                "confidence": round(100 - abs(1 - fusion["multiplier"]) * 100),
                "fusion_method": "CDCF + XGBoost",
            },
            "findings": all_findings,
            "forensics": forensics,
            "ltca_data": ltca_data_payload,
            "heartbeat": heartbeat_data,
            "narrative": narrative,
            "gradcam": None,  # populated separately if image
            "audio": {
                "clone_probability": round(aas, 1) if category in ("audio", "video") else None,
                "anomalies": [f.get("detail", "") for f in aas_f],
            },
            "metadata": forensics.get("metadata", {}),
            "elapsed_seconds": elapsed,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }



# Singleton
orchestrator = DetectionOrchestrator()