from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from loguru import logger
from backend.api.v1.endpoints.analyze import results_store
from backend.services.report.pdf_generator import PdfGenerator

router = APIRouter()
pdf_gen = PdfGenerator()


@router.get("/{analysis_id}")
async def get_report(analysis_id: str):
    """Generate and download the forensic PDF report for an analysis."""
    result = results_store.get(analysis_id)
    if not result:
        raise HTTPException(status_code=404, detail="Analysis not found — run an analysis first")

    logger.info(f"Generating PDF report for: {analysis_id}")
    pdf_buf = pdf_gen.create_report(result)

    filename = f"DeepScan_Report_{analysis_id}.pdf"
    return StreamingResponse(
        pdf_buf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )