import asyncio
import os
import sys
from loguru import logger

# Add backend to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.detection.orchestrator import orchestrator
from backend.utils.hf_api import HF_API_TOKEN

async def test_pipeline():
    logger.info("Starting Deepscan High-Accuracy Pipeline Verification...")
    
    if not HF_API_TOKEN:
        logger.error("HF_API_TOKEN not found in environment. Test will likely fail.")
        return

    # 1. Test Image Detector (Async)
    # We'll use a dummy path, but the logic should trigger HF call
    logger.info("Testing Image Detection logic...")
    # (In a real test we'd use a real small image, here we verify orchestrator load)
    loaded = await orchestrator.load_models()
    if loaded:
        logger.info("Orchestrator models loaded successfully.")
    else:
        logger.error("Failed to load orchestrator models.")

    # 2. Test Text Detector
    logger.info("Testing Text Detection...")
    text = "This is a completely normal human sentence for testing purposes."
    score = await orchestrator.text_detector.analyze(text)
    logger.info(f"AI Text Score for human text: {score}")

    text_ai = "As an AI language model, I can generate text that looks very realistic."
    score_ai = await orchestrator.text_detector.analyze(text_ai)
    logger.info(f"AI Text Score for AI-sounding text: {score_ai}")

    # 3. Test Metadata Fallback
    logger.info("Testing Metadata Extractor fallback...")
    # Use the script itself as a dummy file for metadata
    meta = orchestrator.metadata_extractor.extract(__file__)
    logger.info(f"Extracted metadata (fallback check): {list(meta.keys())[:5]}")

    logger.info("Verification script complete.")

if __name__ == "__main__":
    asyncio.run(test_pipeline())
