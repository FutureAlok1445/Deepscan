import os
from PIL import Image
from PIL.ExifTags import TAGS
from loguru import logger

class MetadataExtractor:
    """
    Layer 2: Extracts hidden image metadata.
    Provides Context Verification Score (CVS) based on metadata anomalies.
    """
    def __init__(self):
        # Known photo editing tools that raise suspicion 
        self.suspicious_software = [
            "photoshop", "gimp", "snapseed", "lightroom", "faceapp", "canva", "midjourney", "dall-e"
        ]

    def extract_metadata(self, image_path: str) -> dict:
        metadata = {
            "camera_model": None,
            "software": None,
            "timestamp": None,
            "gps": [],
            "score_cvs": 0.0, # 0 = highly suspicious, 100 = authentic
            "anomalies": []
        }
        
        try:
            img = Image.open(image_path)
            exif_data = img._getexif()
            
            if not exif_data:
                metadata["score_cvs"] = 90.0
                return metadata
                
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name == "Model":
                    metadata["camera_model"] = str(value).strip()
                elif tag_name == "Software":
                    metadata["software"] = str(value).strip()
                elif tag_name == "DateTimeOriginal":
                    metadata["timestamp"] = str(value).strip()
                elif tag_name == "GPSInfo":
                    metadata["gps"] = "Present"
            
            # Heuristic Scoring
            score = 100.0
            
            if metadata["software"]:
                soft_lower = metadata["software"].lower()
                if any(s in soft_lower for s in self.suspicious_software):
                    score -= 50
                    metadata["anomalies"].append(f"Suspicious editing software detected: {metadata['software']}")
            else:
                pass # No software is fine, could be raw or stripped
                
            if not metadata["camera_model"]:
                pass # No camera model is fine, could be stripped EXIF

            if not metadata["gps"]:
                pass # No GPS is fine
                
            metadata["score_cvs"] = max(0.0, score)
                
        except Exception as e:
            logger.warning(f"Error extracting metadata from {image_path}: {e}")
            metadata["score_cvs"] = 90.0  # Safe fallback
            metadata["anomalies"].append("Error reading metadata headers")
            
        return metadata

metadata_extractor = MetadataExtractor()
