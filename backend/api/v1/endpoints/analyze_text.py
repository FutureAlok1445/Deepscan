from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
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

@router.post("")
@limiter.limit("5/minute")
async def analyze_text(request: Request, body: TextAnalysisRequest):
    """Analyze text for AI generation probability or Phishing risk."""
    text = body.text
    mode = body.mode.lower()
    
    if not text or len(text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text is too short for analysis (minimum 10 characters).")

    logger.info(f"Analyzing text (mode: {mode}, length: {len(text)})")
    
    try:
        start_time = time.time()
        
        if mode == "phishing":
            logger.info("Entering phishing analysis mode...")
            results = await text_detector.analyze_phishing(text)
            logger.info("Phishing analysis complete.")
            overall_score = results["phishing_score"]
            verdict = _get_phishing_verdict(overall_score)
        else:
            logger.info("Entering AI analysis mode...")
            results = await text_detector.analyze_detailed(text)
            logger.info("AI analysis complete.")
            overall_score = results["ai_score"]
            verdict = _get_ai_verdict(overall_score)
        
        execution_time = round(time.time() - start_time, 2)
        
        response = {
            "id": str(uuid.uuid4()),
            "type": mode,
            "text_snippet": text[:100] + "..." if len(text) > 100 else text,
            "overall_score": overall_score,
            "verdict": verdict,
            "timestamp": time.time(),
            "execution_time": execution_time,
            "details": results
        }
        
        return JSONResponse(content=response)
    except Exception as e:
        logger.error(f"Text analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")

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
