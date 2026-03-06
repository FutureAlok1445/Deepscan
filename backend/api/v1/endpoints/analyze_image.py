import hashlib
import mimetypes
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends, BackgroundTasks
from loguru import logger
from typing import Optional

from backend.services.IMageDetector.orchestrator import image_orchestrator
from backend.utils.rate_limiter import limiter
from fastapi.requests import Request

from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import crud
import shutil
import tempfile
import os

router = APIRouter()

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB

async def process_and_update(
    scan_id: str, 
    tmp_path: str, 
    context_caption: str, 
    db: Session
):
    """Background task to run the heavy ML models and update the DB."""
    try:
        # Mocking an UploadFile object for the orchestrator
        class MockFile:
            def __init__(self, path):
                self.path = path
            async def read(self):
                with open(self.path, "rb") as f:
                    return f.read()

        mock_file = MockFile(tmp_path)
        result = await image_orchestrator.process_image(mock_file, context_caption)
        
        crud.update_scan_result(
            db=db,
            scan_id=scan_id,
            status="done",
            ai_score=result["score"],
            verdict=result["verdict"],
            signals=result["signals"],
            regions_json=result["explainability"].get("regions", []),
            heatmap_base64=result["explainability"]["ela_base64_heatmap_prefix"],
            explainability_text=result["explainability"]["text"]
        )
    except Exception as e:
        logger.error(f"Background task failed for {scan_id}: {e}")
        crud.update_scan_result(db, scan_id, status="failed")
    finally:
        # Cleanup temp file
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


@router.post("/image")
@limiter.limit("5/minute")
async def analyze_image_endpoint(
    request: Request,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    context_caption: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Data Acquisition Layer (Layer 1) for Image Deepfake Detection.
    Instantly returns a job_id and processes the ML pipelines in the background.
    """
    logger.info(f"Received async image analysis request: {file.filename}")
    
    file.file.seek(0, 2)
    file_size = file.file.tell()
    file.file.seek(0)
    
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_FILE_SIZE/1024/1024}MB limit.")
        
    mime_type = file.content_type or mimetypes.guess_type(file.filename or "")[0] or "application/octet-stream"
    
    if mime_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported file type: {mime_type}. Allowed: JPEG, PNG, WEBP.")

    # Save to temp file strictly for the background task to read from
    try:
        fd, tmp_path = tempfile.mkstemp(suffix=".jpg")
        with os.fdopen(fd, "wb") as f_out:
            shutil.copyfileobj(file.file, f_out)
    except Exception as e:
        logger.error(f"Failed to save temp file: {e}")
        raise HTTPException(status_code=500, detail="Could not process file upload.")

    # 1. Create pending DB record
    scan = crud.create_scan(db=db, user_id=None) # Anonymous for now
    
    # 2. Add to background queue
    background_tasks.add_task(
        process_and_update,
        scan_id=scan.id,
        tmp_path=tmp_path,
        context_caption=context_caption,
        db=db
    )
    
    # 3. Return immediately
    return {"status": "pending", "job_id": scan.id}

@router.get("/result/{job_id}")
def get_scan_result(job_id: str, db: Session = Depends(get_db)):
    """Polling endpoint for the frontend to check job status."""
    scan = crud.get_scan(db, job_id)
    if not scan:
        raise HTTPException(status_code=404, detail="Job not found")
        
    if scan.status != "done":
        return {"job_id": scan.id, "status": scan.status}
        
    return {
        "job_id": scan.id,
        "status": scan.status,
        "data": {
            "score": scan.ai_score,
            "verdict": scan.verdict,
            "signals": scan.signals,
            "explainability": {
                "text": scan.explainability_text,
                "ela_base64_heatmap_prefix": scan.heatmap_base64,
                "regions": scan.regions_json
            }
        }
    }
