import sys
import logging
from loguru import logger
sys.path.append('.')
from backend.services.report.pdf_generator import PdfGenerator

result = {
    "id": "test_id",
    "filename": "Image_Scan.jpg",
    "file_type": "image",
    "score": 50.0,
    "aacs_score": 50.0,
    "verdict": "UNCERTAIN",
    "findings": [{"engine": "ELA", "score": 50, "detail": "Test"}],
    "narrative": {"summary": "Test", "eli5": "Test", "technical": "Test"}
}

try:
    pdf_gen = PdfGenerator()
    buf = pdf_gen.create_report(result)
    with open("test.pdf", "wb") as f:
        f.write(buf.read())
    print("PDF generated successfully.")
except Exception as e:
    print(f"FAILED: {e}")
