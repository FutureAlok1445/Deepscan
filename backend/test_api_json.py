import asyncio
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.services.detection.orchestrator import DetectionOrchestrator

async def main():
    orch = DetectionOrchestrator()
    await orch.load_models()
    
    print("=== TESTING VIDEO ===")
    res_video = await orch.process_media('dummy_ui_test.mp4', 'video/mp4')
    print("LTCA Keys:", list(res_video.get('ltca_data', {}).keys()))
    print("NLM present:", 'nlm_report' in res_video.get('ltca_data', {}))
    print("NLM TEXT:", res_video.get('ltca_data', {}).get('nlm_report'))
    
if __name__ == "__main__":
    asyncio.run(main())
