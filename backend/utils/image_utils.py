from loguru import logger

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2 not installed — image resize will be skipped")


def resize_image(path: str, limit: int = 1024) -> str:
    if not HAS_CV2:
        return path
    img = cv2.imread(path)
    if img is not None and max(img.shape[:2]) > limit:
        sc = limit / max(img.shape[:2])
        cv2.imwrite(path, cv2.resize(img, (int(img.shape[1]*sc), int(img.shape[0]*sc)), interpolation=cv2.INTER_AREA))
    return path