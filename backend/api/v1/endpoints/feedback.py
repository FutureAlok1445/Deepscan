"""POST /api/v1/feedback — Submit user feedback on analysis accuracy."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from loguru import logger
from datetime import datetime

router = APIRouter()

# In-memory feedback store
feedback_store: list = []


class FeedbackRequest(BaseModel):
    analysis_id: str
    is_correct: bool
    comment: Optional[str] = ""


@router.post("")
async def submit_feedback(body: FeedbackRequest):
    """Save user feedback on analysis accuracy."""
    try:
        feedback_store.append({
            "analysis_id": body.analysis_id,
            "is_correct": body.is_correct,
            "comment": body.comment or "",
            "created_at": datetime.utcnow().isoformat(),
        })
        logger.info(f"Feedback received for {body.analysis_id}: correct={body.is_correct}")
    except Exception as e:
        logger.warning(f"Feedback save failed: {e}")
    return JSONResponse(content={"ok": True})
