from loguru import logger

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2/numpy not installed — Gabor filter will return empty results")


def build_filters():
    if not HAS_CV2:
        return []
    return [(cv2.getGaborKernel((31, 31), 4.0, t, 10.0, 0.5, 0, ktype=cv2.CV_32F) / (1.5 * cv2.getGaborKernel((31, 31), 4.0, t, 10.0, 0.5, 0, ktype=cv2.CV_32F).sum())) for t in np.arange(0, np.pi, np.pi / 16)]


def process(img, filters):
    if not HAS_CV2 or not filters:
        return img
    accum = np.zeros_like(img)
    for kern in filters:
        np.maximum(accum, cv2.filter2D(img, cv2.CV_8UC3, kern), accum)
    return accum