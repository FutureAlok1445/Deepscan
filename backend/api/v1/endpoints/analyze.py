import asyncio
from fastapi import APIRouter, UploadFile, File, Request, HTTPException
from fastapi.responses import JSONResponse
from loguru import logger
from backend.utils.rate_limiter import limiter
from backend.utils.file_handler import save_upload_file, cleanup_file
from backend.services.detection.orchestrator import orchestrator

router = APIRouter()

# In-memory results store (replace with MongoDB in production)
results_store: dict = {}


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
        result = await orchestrator.process_media(file_path, mime_type)
        result["original_filename"] = file.filename
        # Store result for later retrieval
        results_store[result["id"]] = result
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Analysis pipeline failed")
    finally:
        # Cleanup handled by auto_delete_file, but try immediate cleanup too
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