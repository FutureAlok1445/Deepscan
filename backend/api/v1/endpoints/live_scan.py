import os
import uuid
import tempfile
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from loguru import logger

try:
    import cv2
    import numpy as np
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2/numpy not installed — live scan WebSocket will not function")

from backend.services.detection.orchestrator import orchestrator

router = APIRouter()


@router.websocket("/live")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time webcam frame analysis via WebSocket.

    Client sends JPEG-encoded frames as bytes.
    Server replies with per-frame AACS score.
    """
    await websocket.accept()
    logger.info("Live scan WebSocket connected")

    if not HAS_CV2:
        await websocket.send_json({"error": "cv2 not available — live scan requires OpenCV"})
        await websocket.close()
        return

    # Ensure models are loaded
    if not orchestrator.models_loaded:
        await orchestrator.load_models()

    frame_count = 0
    try:
        while True:
            data = await websocket.receive_bytes()
            frame_count += 1

            # Decode JPEG bytes to image
            nparr = np.frombuffer(data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                await websocket.send_json({"error": "Invalid frame data"})
                continue

            # Save temp frame for analysis
            tmp_path = os.path.join(tempfile.gettempdir(), f"deepscan_live_{uuid.uuid4().hex}.jpg")
            cv2.imwrite(tmp_path, frame)

            try:
                # Quick single-frame analysis (MAS only for speed)
                if orchestrator.image_detector:
                    score = orchestrator.image_detector.predict(tmp_path)
                else:
                    score = 50.0

                verdict = "AUTHENTIC" if score <= 30 else "UNCERTAIN" if score <= 60 else "LIKELY_FAKE" if score <= 85 else "DEFINITELY_FAKE"

                await websocket.send_json({
                    "frame": frame_count,
                    "frame_score": round(score, 1),
                    "verdict": verdict,
                    "state": verdict,
                })
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    except WebSocketDisconnect:
        logger.info(f"Live scan disconnected after {frame_count} frames")
    except Exception as e:
        logger.error(f"Live scan error: {e}")
        try:
            await websocket.close()
        except Exception:
            pass