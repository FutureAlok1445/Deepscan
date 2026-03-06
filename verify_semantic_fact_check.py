import asyncio
import os
import sys
import cv2
import numpy as np

# Ensure backend can be found
sys.path.append(os.getcwd())

from backend.services.detection.orchestrator import DetectionOrchestrator
from unittest.mock import AsyncMock, MagicMock

async def test_semantic_pipeline():
    print("--- Testing Semantic Fact-Checking Pipeline ---")
    
    orchestrator = DetectionOrchestrator()
    await orchestrator.load_models()
    
    # Mock the SemanticAnalyzer to return a specific claim
    # Let's use a claim that is likely to be found in Google Fact Check as FALSE
    orchestrator.semantic_analyzer.describe_and_verify = AsyncMock(return_value={
        "description": "A video showing someone claiming that drinking bleach cures COVID-19.",
        "claims": ["drinking bleach cures COVID-19"]
    })
    
    # Create a dummy video file for the orchestrator to process
    dummy_video = "dummy_semantic_test.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(dummy_video, fourcc, 20.0, (640, 480))
    for _ in range(30):
        frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        out.write(frame)
    out.release()
    
    try:
        print(f"Processing dummy video: {dummy_video}")
        result = await orchestrator.process_media(dummy_video, "video")
        
        print("\nPipeline Result:")
        print(f"Overall AACS Score: {result['aacs_score']}")
        print(f"Verdict: {result['verdict']}")
        
        print("\nContextual Findings:")
        for finding in result['findings']:
            if finding['engine'] == "Semantic-Fact-Check":
                print(f"-> {finding['engine']}: Score={finding['score']}, Detail={finding['detail']}")
        
        # Check if the fact-check was actually triggered
        has_fact_check = any(f['engine'] == "Semantic-Fact-Check" for f in result['findings'])
        if has_fact_check:
            print("\nSUCCESS: Semantic Fact-Checking successfully triggered and integrated.")
        else:
            print("\nWARNING: Semantic Fact-Checking finding not found in results.")
            
    finally:
        if os.path.exists(dummy_video):
            os.remove(dummy_video)

if __name__ == "__main__":
    asyncio.run(test_semantic_pipeline())
