import subprocess
import json
import os
from loguru import logger

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False

class MetadataExtractor:
    def extract(self, file_path: str) -> dict:
        """
        Extracts metadata using ExifTool (primary) or Pillow (fallback).
        Identifies AI-generation software in the process.
        """
        metadata = {}
        
        # 1. Primary: ExifTool (Very detailed, but depends on system install)
        try:
            res = subprocess.run(["exiftool", "-j", file_path], capture_output=True, text=True, timeout=5)
            if res.returncode == 0 and res.stdout:
                metadata = json.loads(res.stdout)[0]
                return metadata
        except Exception:
            logger.debug("ExifTool not available, falling back to Python native extraction.")

        # 2. Fallback: Pillow (For images only, no external dependencies)
        if HAS_PILLOW and file_path.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
            try:
                img = Image.open(file_path)
                info = img._getexif()
                if info:
                    for tag, value in info.items():
                        decoded = TAGS.get(tag, tag)
                        metadata[decoded] = str(value)
                
                # Check for Software/Comment tags manually if _getexif fails (for PNG/WEBP)
                if not metadata:
                    for key, val in img.info.items():
                        metadata[str(key)] = str(val)
            except Exception as e:
                logger.debug(f"Pillow extraction failed: {e}")

        # Basic file info if nothing else
        if not metadata:
            metadata = {
                "Filename": os.path.basename(file_path),
                "FileSize": f"{os.path.getsize(file_path) / 1024:.1f} KB",
                "Source": "Internal Fallback"
            }
            
        return metadata