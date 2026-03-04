import subprocess
import json
from loguru import logger

class MetadataExtractor:
    def extract(self, file_path: str) -> dict:
        try:
            res = subprocess.run(["exiftool", "-j", file_path], capture_output=True, text=True)
            return json.loads(res.stdout)[0] if res.returncode == 0 and res.stdout else {}
        except Exception:
            return {"error": "ExifTool not available"}