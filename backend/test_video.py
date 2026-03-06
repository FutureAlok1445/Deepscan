import asyncio
import cv2
import numpy as np
import os
import sys
from loguru import logger

# Add project root to path so 'backend' module is found
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.services.detection.video.video_orchestrator import VideoOrchestrator

def create_dummy_video(filename="dummy_test.mp4", num_frames=30, fps=30):
    """Creates a simple dummy video with a moving square for testing temporal mechanics."""
    height, width = 256, 256
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))
    
    for i in range(num_frames):
        # Create a blank black frame
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        
        # Add some random 'sensor' noise to test FFT
        noise = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)
        frame = cv2.add(frame, noise)
        
        # Add a moving white square
        x = int(50 + i * (100 / num_frames))
        y = int(100 + np.sin(i * 0.5) * 20)
        cv2.rectangle(frame, (x, y), (x+50, y+50), (255, 255, 255), -1)
        
        out.write(frame)
        
    out.release()
    return filename

async def main():
    logger.info("Initializing VideoOrchestrator test...")
    
    # 1. Create a dummy video
    video_file = create_dummy_video()
    logger.info(f"Created temporary dummy video: {video_file}")
    
    try:
        # 2. Instantiate the orchestrator
        orchestrator = VideoOrchestrator()
        
        # Since we use HF models for spatial, but we might not have the API key in the environment,
        # we'll mock the ImageDetector's predict_async just for this test so the rest of the 
        # complex pipeline (LTCA, Noise, Flow) can be tested locally without network issues.
        async def mock_predict(*args, **kwargs):
            return 25.0 # Mocks a 'low probability fake' spatial score
            
        orchestrator.spatial.image_detector.predict_async = mock_predict
        
        # 3. Process the video
        logger.info("Running video through the full analytical pipeline...")
        mas_score, ltca_data = await orchestrator.process_video(video_file, num_frames=12)
        
        # 4. Output results
        logger.info("=== TEST RESULTS ===")
        logger.info(f"Final MAS Score: {mas_score:.2f}/100")
        logger.info(f"LTCA Suspect? : {ltca_data.get('is_fake', False)}")
        logger.info(f"LTCA Confidence: {ltca_data.get('confidence', 0)}%")
        logger.info(f"LTCA Reason    : {ltca_data.get('reason', 'N/A')}")
        logger.info(f"LTCA Curvature : {ltca_data.get('curvature_score', 0)}")
        logger.info(f"LTCA Variance  : {ltca_data.get('velocity_variance', 0)}")
        if ltca_data.get("trajectory_plot"):
            logger.info(f"Trajectory Line: {len(ltca_data['trajectory_plot'])} data points generated")
        
        logger.info("Test completed successfully. All modules successfully executed.")
        
    except Exception as e:
        logger.error(f"Test failed with exception: {e}")
    finally:
        # Cleanup
        if os.path.exists(video_file):
            os.remove(video_file)
            logger.info(f"Cleaned up {video_file}")

if __name__ == "__main__":
    asyncio.run(main())
