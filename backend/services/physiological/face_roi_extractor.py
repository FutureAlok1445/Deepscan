from loguru import logger

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2 not installed — FaceROIExtractor will return empty results")


class FaceROIExtractor:
    def extract_faces(self, image_path: str):
        if not HAS_CV2:
            return []
        try:
            face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
            return face_cascade.detectMultiScale(cv2.cvtColor(cv2.imread(image_path), cv2.COLOR_BGR2GRAY), 1.1, 4)
        except Exception:
            return []