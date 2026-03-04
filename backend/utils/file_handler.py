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
                     "mp4": "video/mp4", "wav": "audio/wav", "mp3": "audio/mpeg",
                     "m4a": "audio/x-m4a", "webp": "image/webp", "ogg": "audio/ogg"}
        mime = _ext_mime.get(ext, "application/octet-stream")
    if not any([ext in mime for ext in ["jpeg", "png", "mp4", "wav", "mpeg", "x-m4a", "webp", "ogg"]]):
        raise ValueError(f"Invalid type: {mime}")
    path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}.{mime.split('/')[-1]}")
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    with open(path, "wb") as f: f.write(contents)
    if not await scan_with_clamav(path):
        os.remove(path)
        raise ValueError("Malware detected")
    asyncio.create_task(auto_delete_file(path))
    return {"filename": os.path.basename(path), "path": path, "mime_type": mime, "size": len(contents)}

def cleanup_file(file_path: str):
    if os.path.exists(file_path): os.remove(file_path)