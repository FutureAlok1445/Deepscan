import os, tempfile
from loguru import logger

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2/numpy not installed — VideoDetector will return heuristic scores")

_TMPDIR = tempfile.gettempdir()

from backend.services.detection.image_detector import ImageDetector


class VideoDetector:
    def __init__(self):
        self.image_detector = ImageDetector()

    def process_video(self, video_path: str, num_frames=10) -> float:
        if not HAS_CV2:
            return self.image_detector.predict(video_path)  # fallback: treat as image
        try:
            cap = cv2.VideoCapture(video_path)
            total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            scores = []
            for index in (np.linspace(0, total - 1, num_frames, dtype=int) if total >= num_frames else range(max(1, total))):
                cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                ret, frame = cap.read()
                if ret:
                    tmp_frame = os.path.join(_TMPDIR, f"frame_{index}.jpg")
                    cv2.imwrite(tmp_frame, frame)
                    scores.append(self.image_detector.predict(tmp_frame))
                    try:
                        os.remove(tmp_frame)
                    except Exception:
                        pass
            cap.release()
            return sum(scores) / len(scores) if scores else 50.0
        except Exception:
            return 50.0