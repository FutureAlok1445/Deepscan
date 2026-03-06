import os, uuid, asyncio, subprocess, tempfile
from fastapi import UploadFile
from loguru import logger

try:
    import magic
    HAS_MAGIC = True
except ImportError:
    HAS_MAGIC = False
    logger.warning("python-magic not installed — MIME detection will use file extension")

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "deepscan_uploads")


async def auto_delete_file(file_path: str, delay: int = 60):
    await asyncio.sleep(delay)
    if os.path.exists(file_path): os.remove(file_path)

async def scan_with_clamav(file_path: str) -> bool:
    try:
        import shutil
        if shutil.which("clamdscan"):
            if subprocess.run(["clamdscan", "--fdpass", file_path]).returncode != 0: return False
        return True
    except Exception: return True

async def save_upload_file(file: UploadFile) -> dict:
    contents = await file.read()
    # Determine MIME type
    if HAS_MAGIC:
        mime = magic.from_buffer(contents, mime=True)
    else:
        # Fallback: derive MIME from file extension
        ext = (file.filename or "").rsplit(".", 1)[-1].lower() if file.filename else ""
        _ext_mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png",
                     "bmp": "image/bmp", "webp": "image/webp",
                     "mp4": "video/mp4", "avi": "video/x-msvideo", "mov": "video/quicktime",
                     "mkv": "video/x-matroska", "webm": "video/webm",
                     "wav": "audio/wav", "mp3": "audio/mpeg", "flac": "audio/flac",
                     "m4a": "audio/x-m4a", "ogg": "audio/ogg"}
        mime = _ext_mime.get(ext, "application/octet-stream")

    # Validate MIME type
    allowed_prefixes = ("image/", "video/", "audio/")
    if not mime.startswith(allowed_prefixes):
        raise ValueError(f"Invalid file type: {mime}")

    # Map MIME to a clean file extension for storage
    _mime_ext = {
        "image/jpeg": "jpg", "image/png": "png", "image/bmp": "bmp", "image/webp": "webp",
        "video/mp4": "mp4", "video/x-msvideo": "avi", "video/quicktime": "mov",
        "video/x-matroska": "mkv", "video/webm": "webm",
        "audio/wav": "wav", "audio/x-wav": "wav", "audio/mpeg": "mp3",
        "audio/flac": "flac", "audio/x-m4a": "m4a", "audio/ogg": "ogg",
    }
    save_ext = _mime_ext.get(mime, mime.split('/')[-1])
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.{save_ext}")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(path, "wb") as f: f.write(contents)
    if not await scan_with_clamav(path):
        os.remove(path)
        raise ValueError("Malware detected")
    asyncio.create_task(auto_delete_file(path, delay=120))
    return {"filename": os.path.basename(path), "path": path, "mime_type": mime, "size": len(contents)}

def cleanup_file(file_path: str):
    if os.path.exists(file_path): os.remove(file_path)