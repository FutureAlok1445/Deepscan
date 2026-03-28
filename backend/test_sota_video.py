import asyncio
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from backend.services.detection.video.video_orchestrator import VideoOrchestrator

async def test_sota():
    orch = VideoOrchestrator()
    score, ltca, frames, desc_task = await orch.process_video('test_videos/ai_video.mp4')
    print(f'MAS Score: {score}')
    print('SOTA findings:', [f for f in ltca['advanced_findings'] if 'Meso' in f['engine'] or 'Xception' in f['engine']])

if __name__ == '__main__':
    asyncio.run(test_sota())

