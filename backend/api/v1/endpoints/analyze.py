import asyncio
import math
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from backend.utils.rate_limiter import limiter
from backend.utils.file_handler import save_upload_file, cleanup_file
from backend.services.detection.orchestrator import orchestrator

router = APIRouter()

# In-memory results store (replace with MongoDB in production)
results_store: dict = {}


def _sanitize(obj):
    """
    Recursively convert non-JSON-serializable types (NumPy scalars, arrays, NaN/Inf)
    to Python native types. Called before every JSONResponse to prevent 500 errors.
    """
    # Handle numpy types without importing numpy (avoids import overhead here)
    type_name = type(obj).__name__
    module = getattr(type(obj), "__module__", "")

    if "numpy" in module:
        # numpy scalar → Python scalar
        if hasattr(obj, "item"):
            val = obj.item()
            # Replace NaN/Inf with None
            if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
                return None
            return val
        # numpy array → list
        if hasattr(obj, "tolist"):
            return obj.tolist()

    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}

    if isinstance(obj, (list, tuple)):
        return [_sanitize(i) for i in obj]

    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None

    return obj


@router.post("")
@limiter.limit("10/minute")
async def analyze_file(request: Request, file: UploadFile = File(...)):
    """Upload a media file for full AACS deepfake analysis."""
    try:
        file_info = await save_upload_file(file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    file_path = file_info["path"]
    mime_type = file_info["mime_type"]
    logger.info(f"Analyzing file: {file_info['filename']} ({mime_type})")

    try:
        if mime_type.startswith("image/"):
            import uuid
            
            # Create a mock file object that the image_orchestrator can await read() on
            class MockFile:
                def __init__(self, path):
                    self.path = path
                async def read(self):
                    with open(self.path, "rb") as f:
                        return f.read()
                        
            from backend.services.IMageDetector.orchestrator import image_orchestrator
            res = await image_orchestrator.process_image(MockFile(file_path), context_caption=None)
            
            # Map the response into the format expected by the frontend Result page
            analysis_id = str(uuid.uuid4())
            result = {
                "id": analysis_id,
                "status": "complete",
                "aacs_score": res["score"],
                "score": res["score"],
                "verdict": res["verdict"],
                "file_type": mime_type,
                "original_filename": file.filename,
                "findings": [{"engine": k, "score": v, "detail": f"{k} analyzed this layer"} for k, v in res.get("signals", {}).items()],
                "image_data": res, # Retain full 10-layer output
                "cdcf": {
                    "fusion_method": "10-Layer AI Fusion Stack",
                    "confidence": 95,
                    "multiplier": 1.0,
                },
                "narrative": {
                    "summary": res.get("explainability", {}).get("text", "No detailed summary provided."),
                    "detailed": "10-Layer Image Deepfake Architecture activated for this scan.",
                }
            }
        else:
            result = await orchestrator.process_media(file_path, mime_type)
            result["original_filename"] = file.filename
            
        # Sanitize all NumPy types before JSON encoding (prevents 500 on np.float64 etc.)
        result = _sanitize(result)
        # Store result for later retrieval
        results_store[result["id"]] = result
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis pipeline failed: {str(e)}")
    finally:
        try:
            cleanup_file(file_path)
        except Exception:
            pass


@router.get("/{analysis_id}")
async def get_analysis_result(analysis_id: str):
    """Retrieve a previously completed analysis result."""
    result = results_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return JSONResponse(content=result)
