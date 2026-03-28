from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
import math

from pydantic import BaseModel
from loguru import logger
from backend.utils.rate_limiter import limiter
from backend.services.detection.text_detector import TextDetector
import uuid
import time

router = APIRouter()
text_detector = TextDetector()

class TextAnalysisRequest(BaseModel):
    text: str
    mode: str = "ai"
    language: str = "en"

@router.post("")
@limiter.limit("10/minute")
async def analyze_text(request: Request, body: TextAnalysisRequest):
    """Analyze text for AI generation probability or Phishing risk.
    
    NEVER returns HTTP 500. All errors are caught and returned as valid JSON.
    """
    analysis_id = str(uuid.uuid4())
    text = body.text
    mode = body.mode.lower()
    start_time = time.time()
    word_count = len(text.split()) if text else 0
    
    if not text or len(text.strip()) < 10:
        return JSONResponse(content={
            "id": analysis_id,
            "type": mode,
            "text_snippet": text[:100] if text else "",
            "overall_score": 0.0,
            "score": 0.0,
            "aacs_score": 0.0,
            "verdict": "Text Too Short",
            "word_count": word_count,
            "timestamp": time.time(),
            "execution_time": 0.0,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {
                "signals": {"hf_model": 0, "perplexity": 0, "burstiness": 0, "sapling_api": 0},
                "reasons": ["Text is too short for reliable analysis (minimum 10 characters)."]
            }
        })

    logger.info(f"[{analysis_id}] Analyzing text (mode: {mode}, length: {len(text)}, words: {word_count})")
    
    try:
        if mode == "phishing":
            results = await text_detector.analyze_phishing(text)
            overall_score = results.get("phishing_score", 0.0)
            verdict = _get_phishing_verdict(overall_score)
        else:
            results = await text_detector.analyze_detailed(text)
            overall_score = results.get("ai_score", 0.0)
            verdict = _get_ai_verdict(overall_score)
        
        execution_time = round(time.time() - start_time, 2)
        
        # Ensure signals exist in results
        if "signals" not in results:
            results["signals"] = {"hf_model": 0, "perplexity": 0, "burstiness": 0, "sapling_api": 0}
        if "reasons" not in results:
            results["reasons"] = ["Analysis complete."]
        
        response = {
            "id": analysis_id,
            "type": mode,
            "text_snippet": text[:100] + "..." if len(text) > 100 else text,
            "overall_score": round(overall_score, 2),
            "score": round(overall_score, 2),
            "aacs_score": round(overall_score, 2),
            "verdict": verdict,
            "word_count": word_count,
            "timestamp": time.time(),
            "execution_time": execution_time,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": results
        }
        
        logger.info(f"[{analysis_id}] Text analysis complete: score={overall_score:.1f}, verdict={verdict}")
        return JSONResponse(content=_sanitize(response))
        
    except Exception as e:
        logger.error(f"[{analysis_id}] Text analysis failed: {e}", exc_info=True)
        elapsed = round(time.time() - start_time, 2)
        return JSONResponse(content={
            "id": analysis_id,
            "type": mode,
            "text_snippet": text[:100] + "..." if len(text) > 100 else text,
            "overall_score": 50.0,
            "score": 50.0,
            "aacs_score": 50.0,
            "verdict": "Analysis Error",
            "word_count": word_count,
            "timestamp": time.time(),
            "execution_time": elapsed,
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "details": {
                "signals": {"hf_model": 0, "perplexity": 0, "burstiness": 0, "sapling_api": 0},
                "reasons": [f"Analysis encountered an error: {str(e)[:150]}"]
            },
            "error": str(e)[:200]
        })

def _sanitize(obj):
    """
    Recursively convert non-JSON-serializable types (NumPy scalars, arrays, NaN/Inf)
    to Python native types.
    """
    # Handle numpy types
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

    return obj

def _get_ai_verdict(score: float) -> str:
    if score < 30:
        return "Human Written"
    elif score < 60:
        return "Uncertain"
    elif score < 82:
        return "Likely AI Generated"
    else:
        return "Definitely AI Generated"

def _get_phishing_verdict(score: float) -> str:
    if score < 20:
        return "Safe Content"
    elif score < 45:
        return "Low Phishing Risk"
    elif score < 75:
        return "High Phishing Risk"
    else:
        return "Definite Phishing"
