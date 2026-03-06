import asyncio
import cv2
import numpy as np
from backend.services.detection.image_detector import ImageDetector

async def test_image():
    detector = ImageDetector()
    print("Starting Multi-Engine Image Analysis on standard test face (Lena)...")
    score, findings = await detector.predict_async("test_face.jpg")
    
    print("\n--- RESULTS ---")
    print(f"Final Image Score: {score:.2f}%")
    for f in findings:
        print(f"Engine: {f['engine']} | Score: {f['score']} | Detail: {f['detail']}")

if __name__ == "__main__":
    asyncio.run(test_image())
