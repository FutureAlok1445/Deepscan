"""
Lightweight standalone server for the 10-Layer Image Deepfake Detector.
Run with:  python -m uvicorn backend.services.IMageDetector.server --host 127.0.0.1 --port 8000 --reload
"""
import contextlib
import mimetypes
import io

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.requests import Request
from loguru import logger
from typing import Optional

from backend.services.IMageDetector.orchestrator import image_orchestrator

ALLOWED_MIME_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_FILE_SIZE = 15 * 1024 * 1024  # 15 MB


@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Image Detector standalone server...")
    try:
        await image_orchestrator.load_models()
        logger.info("IMageDetector models loaded.")
    except Exception as e:
        logger.warning(f"Model preload skipped (will use heuristics): {e}")
    yield
    logger.info("Shutting down Image Detector server...")


app = FastAPI(
    title="DeepScan Image Detector",
    version="1.0.0",
    description="Standalone 10-Layer Image Deepfake Detection API",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/v1/analyze/image")
async def analyze_image(
    request: Request,
    file: UploadFile = File(...),
    context_caption: Optional[str] = Form(None),
):
    logger.info(f"Received image: {file.filename}")

    # Size check
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)
    if size > MAX_FILE_SIZE:
        raise HTTPException(413, detail="File too large (15 MB max).")

    # MIME check
    mime = file.content_type or mimetypes.guess_type(file.filename or "")[0] or ""
    if mime not in ALLOWED_MIME_TYPES:
        raise HTTPException(415, detail=f"Unsupported type: {mime}")

    try:
        result = await image_orchestrator.process_image(file, context_caption)
        return {"status": "success", "data": result}
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        raise HTTPException(500, detail=str(e))


@app.get("/health")
async def health():
    return {"status": "ok", "service": "IMageDetector Standalone"}
