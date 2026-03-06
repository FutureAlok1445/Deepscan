from fastapi import APIRouter, Query, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import desc
from backend.db.database import get_db
from backend.db import models
from typing import List

router = APIRouter()

@router.get("")
async def get_history(
    limit: int = Query(20, ge=1, le=100), 
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Return analysis history from the persistent database, newest first."""
    query = db.query(models.Scan).order_by(desc(models.Scan.created_at))
    total = query.count()
    scans = query.offset(offset).limit(limit).all()

    items = []
    for s in scans:
        items.append({
            "id": s.id,
            "status": s.status,
            "score": s.ai_score,
            "verdict": s.verdict,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "explainability_summary": s.explainability_text[:100] + "..." if s.explainability_text else None,
        })

    return {
        "items": items, 
        "total": total, 
        "limit": limit, 
        "offset": offset
    }

@router.get("/{job_id}")
async def get_history_detail(job_id: str, db: Session = Depends(get_db)):
    """Fetch full details for a specific past scan."""
    scan = db.query(models.Scan).filter(models.Scan.id == job_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    return {
        "id": scan.id,
        "status": scan.status,
        "data": {
            "score": scan.ai_score,
            "verdict": scan.verdict,
            "signals": scan.signals,
            "explainability": {
                "text": scan.explainability_text,
                "ela_base64_heatmap_prefix": scan.heatmap_base64
            }
        },
        "created_at": scan.created_at.isoformat() if scan.created_at else None
    }