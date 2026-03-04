import os
from loguru import logger

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2 not installed — video frame extraction will be unavailable")


def extract_frames(path: str, out_dir: str, num_frames: int = 10) -> list:
    if not HAS_CV2:
        return []
    os.makedirs(out_dir, exist_ok=True)
    cap = cv2.VideoCapture(path)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    extracted = []
    if total > 0:
        for idx, f_idx in enumerate([int(i * total / num_frames) for i in range(num_frames)]):
            cap.set(cv2.CAP_PROP_POS_FRAMES, f_idx)
            ret, frame = cap.read()
            if ret:
                p = os.path.join(out_dir, f"frame_{idx}.jpg")
                cv2.imwrite(p, frame)
                extracted.append(p)
    cap.release()
    return extracted