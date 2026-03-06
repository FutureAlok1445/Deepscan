from sqlalchemy.orm import Session
from . import models

def create_scan(db: Session, user_id: str = None) -> models.Scan:
    """Creates a new pending scan record in the database."""
    db_scan = models.Scan(
        user_id=user_id,
        status="pending"
    )
    db.add(db_scan)
    db.commit()
    db.refresh(db_scan)
    return db_scan

def get_scan(db: Session, scan_id: str) -> models.Scan:
    """Retrieves a scan by ID."""
    return db.query(models.Scan).filter(models.Scan.id == scan_id).first()

def update_scan_result(
    db: Session, 
    scan_id: str, 
    status: str, 
    ai_score: float = None,
    verdict: str = None,
    signals: dict = None,
    regions_json: list = None,
    heatmap_base64: str = None,
    explainability_text: str = None
) -> models.Scan:
    """Updates a scan with completed processing results."""
    db_scan = get_scan(db, scan_id)
    if db_scan:
        db_scan.status = status
        db_scan.ai_score = ai_score
        db_scan.verdict = verdict
        db_scan.signals = signals
        db_scan.regions_json = regions_json
        db_scan.heatmap_base64 = heatmap_base64
        db_scan.explainability_text = explainability_text
        db.commit()
        db.refresh(db_scan)
    return db_scan
