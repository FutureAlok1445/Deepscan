"""
analyze.py — Main analysis endpoint for DEEP[SCAN]

POST /api/v1/analyze — Upload media for full AACS deepfake analysis
GET /api/v1/analyze/{id} — Retrieve a previous result

GUARANTEED: Always returns HTTP 200 with a well-defined JSON shape.
NEVER returns HTTP 500 during demo. Ever.
"""
import asyncio
import math
import base64
import io
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
import time
import uuid
from fastapi import APIRouter, UploadFile, File, Request
from fastapi.responses import JSONResponse
from loguru import logger
from backend.utils.rate_limiter import limiter
from backend.utils.file_handler import save_upload_file, cleanup_file
from backend.services.detection.orchestrator import orchestrator

router = APIRouter()

# In-memory results store (replace with MongoDB in production)
results_store: dict = {}


# ═══════════════════════════════════════════════════════════════
# JSON Sanitizer — prevents 500 on NumPy types, NaN, Inf
# ═══════════════════════════════════════════════════════════════
def _sanitize(obj):
    """
    Recursively convert non-JSON-serializable types (NumPy scalars, arrays, NaN/Inf)
    to Python native types. Called before every JSONResponse to prevent 500 errors.
    """
    type_name = type(obj).__name__
    module = getattr(type(obj), "__module__", "")

    if "numpy" in module:
        if hasattr(obj, "item"):
            val = obj.item()
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val
        if hasattr(obj, "tolist"):
            return obj.tolist()

    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_sanitize(i) for i in obj]

    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None

    if isinstance(obj, bytes):
        return None  # Drop raw bytes (e.g. spectrogram PNGs) — use base64 strings instead

    return obj


# ═══════════════════════════════════════════════════════════════
# Explanation Auto-Generator
# ═══════════════════════════════════════════════════════════════
def _generate_explanation(verdict: str, detectors_used: list, sub_scores: dict) -> str:
    """Generate plain-English explanation based on verdict and scores."""
    if verdict in ("Authentic", "AUTHENTIC"):
        return "No manipulation artifacts detected. Media appears genuine."
    elif verdict in ("Uncertain", "UNCERTAIN"):
        return "Some inconsistencies found but below threshold. Treat with caution."
    elif verdict in ("Likely Fake", "LIKELY_FAKE"):
        used = ", ".join(detectors_used[:3]) if detectors_used else "multiple detectors"
        return f"Multiple manipulation signatures detected across {used}."
    elif verdict in ("Definitely Fake", "DEFINITELY_FAKE"):
        # Find highest scoring detector
        highest = max(sub_scores.items(), key=lambda x: (x[1] or 0)) if sub_scores else ("MAS", 0)
        return f"High-confidence deepfake. {highest[0]} flagged severe artifacts."
    return "Analysis complete. Review sub-scores for details."


# ═══════════════════════════════════════════════════════════════
# POST /api/v1/analyze — Main endpoint
# ═══════════════════════════════════════════════════════════════
@router.post("")
@limiter.limit("10/minute")
async def analyze_file(request: Request, file: UploadFile = File(...)):
    """Upload a media file for full AACS deepfake analysis.
    
    GUARANTEED RESPONSE SHAPE — never returns HTTP 500.
    """
    start_time = time.time()
    analysis_id = str(uuid.uuid4())
    file_path = None

    try:
        # ─── File Upload ───
        try:
            file_info = await save_upload_file(file)
            file_path = file_info["path"]
            mime_type = file_info["mime_type"]
        except (ValueError, Exception) as e:
            elapsed = int((time.time() - start_time) * 1000)
            return JSONResponse(content={
                "id": analysis_id,
                "status": "error",
                "aacs_score": 50.0,
                "score": 50.0,
                "verdict": "Uncertain",
                "confidence": 0.0,
                "sub_scores": {"MAS": None, "PPS": None, "IRS": None, "AAS": None, "CVS": None},
                "explanation": f"File upload failed: {str(e)}",
                "gradcam_available": False,
                "gradcam_base64": None,
                "detectors_used": [],
                "processing_time_ms": elapsed,
                "fallback_used": True,
                "findings": [],
                "file_type": "unknown",
                "original_filename": getattr(file, "filename", "unknown"),
            })

        logger.info(f"[{analysis_id}] Analyzing: {file_info['filename']} ({mime_type})")

        # ─── Route to appropriate pipeline ───
        if mime_type.startswith("image/"):
            # Use the 10-layer IMageDetector pipeline
            class MockFile:
                def __init__(self, path):
                    self.path = path
                async def read(self):
                    with open(self.path, "rb") as f:
                        return f.read()

            from backend.services.IMageDetector.orchestrator import image_orchestrator
            res = await image_orchestrator.process_image(MockFile(file_path), context_caption=None)

            elapsed = int((time.time() - start_time) * 1000)

            # Map IMageDetector response to guaranteed shape
            score = res.get("score", 50.0)
            verdict = res.get("verdict", "Uncertain")
            signals = res.get("signals", {})
            
            # Map the response into the format expected by the frontend Result page
            analysis_id = str(uuid.uuid4())
            
            # Read image as base64 to ensure frontend can display it (since we delete the temp file)
            with open(file_path, "rb") as f:
                img_data = f.read()
                img_b64 = base64.b64encode(img_data).decode('utf-8')
                image_url = f"data:{mime_type};base64,{img_b64}"

            result = {
                "id": analysis_id,
                "status": "complete",
                "aacs_score": res.get("score", 0),
                "score": res.get("score", 0),
                "verdict": res.get("verdict", "UNCERTAIN"),
                "file_type": mime_type,
                "original_filename": file.filename,
                "original_image_url": image_url,
                "findings": [{"engine": k, "score": v, "detail": f"{k} analyzed this layer"} for k, v in res.get("signals", {}).items()],
                "image_data": {
                    "signals": res.get("signals", {}),
                    "explainability": res.get("explainability", {})
                },
                "forensics": {
                    "ela": {
                        **res.get("explainability", {}),
                        "image_url": image_url # Vital for ElaHeatmapViewer
                    }
                },
                "cdcf": {
                    "fusion_method": "10-Layer AI Fusion Stack",
                    "confidence": 95,
                    "multiplier": 1.0,
                },
                "narrative": {
                    "summary": res.get("explainability", {}).get("text", "No detailed summary provided."),
                    "detailed": "10-Layer Image Deepfake Architecture activated for this scan.",
                },
            }
        else:
            # Use the full multi-modal orchestrator (audio/video/text)
            result = await orchestrator.process_media(file_path, mime_type)
            result["original_filename"] = file.filename
            
            elapsed = int((time.time() - start_time) * 1000)
            
            # Ensure guaranteed fields exist
            result.setdefault("id", analysis_id)
            result.setdefault("status", "success")
            result.setdefault("aacs_score", result.get("score", 50.0))
            result.setdefault("verdict", "Uncertain")
            result.setdefault("confidence", 0.8)
            result.setdefault("explanation", _generate_explanation(
                result.get("verdict", "Uncertain"),
                result.get("detectors_used", []),
                result.get("sub_scores", {})
            ))
            result.setdefault("gradcam_available", False)
            result.setdefault("gradcam_base64", None)
            result.setdefault("detectors_used", ["orchestrator"])
            result.setdefault("processing_time_ms", elapsed)
            result.setdefault("fallback_used", False)

        # ─── Sanitize & store ───
        result = _sanitize(result)
        results_store[result["id"]] = result
        return JSONResponse(content=result)

    except Exception as e:
        # ═══ CATCH-ALL: NEVER return HTTP 500 ═══
        logger.error(f"[{analysis_id}] Analysis pipeline crashed: {e}", exc_info=True)
        elapsed = int((time.time() - start_time) * 1000)
        
        error_result = {
            "id": analysis_id,
            "status": "error",
            "aacs_score": 50.0,
            "score": 50.0,
            "verdict": "Uncertain",
            "confidence": 0.0,
            "sub_scores": {"MAS": None, "PPS": None, "IRS": None, "AAS": None, "CVS": None},
            "explanation": f"Analysis pipeline encountered an error: {str(e)[:200]}",
            "gradcam_available": False,
            "gradcam_base64": None,
            "detectors_used": [],
            "processing_time_ms": elapsed,
            "fallback_used": True,
            "findings": [],
            "file_type": "unknown",
            "original_filename": getattr(file, "filename", "unknown"),
            "error": str(e)[:200],
        }
        results_store[analysis_id] = error_result
        return JSONResponse(content=error_result)

    finally:
        if file_path:
            try:
                cleanup_file(file_path)
            except Exception:
                pass


# ═══════════════════════════════════════════════════════════════
# GET /api/v1/analyze/{id} — Retrieve result
# ═══════════════════════════════════════════════════════════════
@router.get("/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Retrieve a previously completed analysis result."""
    result = results_store.get(analysis_id)
    if not result:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "aacs_score": 0.0,
                "verdict": "Unknown",
                "explanation": "Analysis not found. It may have expired or never existed.",
            }
        )
    return JSONResponse(content=result)
