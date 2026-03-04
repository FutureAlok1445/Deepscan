import time
import uuid
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

# In-memory community alerts store
community_alerts: list = [
    {
        "id": "alert-001",
        "title": "Deepfake election ad circulating on WhatsApp",
        "content": "AI-generated video of political leader making false promises spotted in multiple groups.",
        "tags": ["politics", "video", "whatsapp"],
        "trust_score": -15,
        "verified": True,
        "submitted_by": "community",
        "created_at": "2024-12-15T10:30:00Z",
    },
    {
        "id": "alert-002",
        "title": "Fake celebrity endorsement images on Instagram",
        "content": "Multiple GAN-generated images of Bollywood celebrities endorsing crypto schemes.",
        "tags": ["celebrity", "image", "instagram"],
        "trust_score": -22,
        "verified": True,
        "submitted_by": "community",
        "created_at": "2024-12-14T08:15:00Z",
    },
    {
        "id": "alert-003",
        "title": "Voice-cloned phone scam targeting elderly",
        "content": "AI-cloned voices used to impersonate family members requesting money transfers.",
        "tags": ["audio", "scam", "voice-clone"],
        "trust_score": -30,
        "verified": False,
        "submitted_by": "community",
        "created_at": "2024-12-13T14:45:00Z",
    },
]


class CommunityPost(BaseModel):
    title: str
    content: str
    tags: list
    submitted_by: Optional[str] = "anonymous"


@router.get("")
async def list_community_alerts(limit: int = 20, offset: int = 0):
    """List community-submitted deepfake alerts."""
    return {
        "items": community_alerts[offset : offset + limit],
        "total": len(community_alerts),
    }


@router.post("")
async def create_community_alert(post: CommunityPost):
    """Submit a new community alert about suspected deepfakes."""
    alert = {
        "id": f"alert-{uuid.uuid4().hex[:8]}",
        "title": post.title,
        "content": post.content,
        "tags": post.tags,
        "trust_score": 0,
        "verified": False,
        "submitted_by": post.submitted_by,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    community_alerts.insert(0, alert)
    return {"status": "success", "alert": alert}


@router.get("/stats")
async def community_stats():
    """Return community alert statistics."""
    total = len(community_alerts)
    verified = sum(1 for a in community_alerts if a.get("verified"))
    return {
        "total_alerts": total,
        "verified_alerts": verified,
        "unverified_alerts": total - verified,
        "avg_trust_score": sum(a.get("trust_score", 0) for a in community_alerts) / max(total, 1),
    }