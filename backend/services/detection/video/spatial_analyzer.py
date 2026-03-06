import os
import cv2
import tempfile
from loguru import logger
from backend.services.detection.image_detector import ImageDetector

_TMPDIR = tempfile.gettempdir()

class SpatialAnalyzer:
    def __init__(self):
        self.image_detector = ImageDetector()
        
    async def analyze_frames(self, frames: list) -> float:
        """
        Runs ViT spatial analysis on a list of key frames.
        Returns the average Deepfake probability (0-100).
        """
        if not frames:
            return 50.0
            
        spatial_scores = []
        for i, frame in enumerate(frames):
            tmp_frame = os.path.join(_TMPDIR, f"spatial_vframe_{i}.jpg")
            try:
                cv2.imwrite(tmp_frame, frame)
                score = await self.image_detector.predict_async(tmp_frame)
                spatial_scores.append(score)
            except Exception as e:
                logger.error(f"Spatial frame analysis failed: {e}")
            finally:
                if os.path.exists(tmp_frame):
                    try:
                        os.remove(tmp_frame)
                    except:
                        pass
                        
        if spatial_scores:
            return sum(spatial_scores) / len(spatial_scores)
        return 50.0
