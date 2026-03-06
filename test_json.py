import asyncio
import json
from backend.services.detection.image_detector import ImageDetector

async def run():
    a = ImageDetector()
    s, f = await a.predict_async('test_face.jpg')
    with open('clean_output.json', 'w', encoding='utf-8') as file:
        json.dump({'score': s, 'findings': f}, file, indent=2)

asyncio.run(run())
