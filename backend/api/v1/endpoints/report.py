from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from loguru import logger
from backend.api.v1.endpoints.analyze import results_store
from backend.services.report.pdf_generator import PdfGenerator
from sqlalchemy.orm import Session
from backend.db.database import get_db
from backend.db import crud

router = APIRouter()
pdf_gen = PdfGenerator()


@router.get("/{analysis_id}")
async def get_report(
    analysis_id: str, 
    score: float = None, 
    verdict: str = None, 
    db: Session = Depends(get_db)
):
    """Generate and download the forensic PDF report for an analysis."""
    result = results_store.get(analysis_id)
    if not result:
        # Check database for scan
        scan = crud.get_scan(db, analysis_id)
        if not scan:
            raise HTTPException(status_code=404, detail="Analysis not found — run an analysis first")
            
        signals = scan.signals or {}
        # Reconstruct result dict expected by pdf_generator
        result = {
            "id": scan.id,
            "filename": "Image_Scan.jpg",
            "file_type": "image",
            "score": scan.ai_score,
            "aacs_score": scan.ai_score,
            "verdict": scan.verdict,
            "elapsed_seconds": 0,
            "sub_scores": {
                "mas": 100 - signals.get("visual_forensics_mas", 50),
                "pps": 100 - signals.get("face_geometry_pps", 50),
                "freq": 100 - signals.get("frequency", 50),
                "cvs": signals.get("metadata_cvs", 50),
                "diffusion": 100 - signals.get("diffusion_fingerprint", 50)
            },
            "findings": [
                {"engine": "ELA", "score": 100 - signals.get("visual_forensics_mas", 50), "detail": "Image pixel block manipulation"},
                {"engine": "FACE", "score": 100 - signals.get("face_geometry_pps", 50), "detail": "Face geometry proportions"},
                {"engine": "FREQ", "score": 100 - signals.get("frequency", 50), "detail": "Frequency artifacts"},
            ],
            "forensics": {
                "ela": {"ela_score": 100 - signals.get("visual_forensics_mas", 50), "analysis_note": "Visual forensics MAS score" },
                "fft": {"fft_score": 100 - signals.get("frequency", 50) }
            },
            "heartbeat": {},
            "narrative": {
                "summary": "Forensic analysis completed via Deepscan Image ML backend.",
                "eli5": f"This image received an AI probability score of {scan.ai_score:.1f}/100.",
                "technical": scan.explainability_text or "No deep technical explanation available."
            }
        }

    # Override with frontend visual parameters if provided
    if score is not None:
        result["aacs_score"] = score
        result["score"] = score
    if verdict:
        result["verdict"] = verdict.upper().replace(' ', '_')

    logger.info(f"Generating PDF report for: {analysis_id}")
    pdf_buf = pdf_gen.create_report(result)

    filename = f"DeepScan_Report_{analysis_id}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )