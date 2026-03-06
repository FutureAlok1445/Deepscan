import traceback

def test_audio_deepfake_detector():
    try:
        import librosa
        import torch
        from transformers import pipeline
        import numpy as np

        print(f"Loading model MelodyMachine/Deepfake-Audio-Detection...")
        device = 0 if torch.cuda.is_available() else -1
        pipe = pipeline("audio-classification", model="MelodyMachine/Deepfake-Audio-Detection", device=device)
        
        print("Model loaded. Running dummy inference...")
        target_sr = pipe.feature_extractor.sampling_rate if hasattr(pipe, "feature_extractor") else 16000
        audio = np.random.uniform(-1, 1, target_sr).astype(np.float32)
        
        predictions = pipe(audio)
        print(f"Predictions: {predictions}")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    test_audio_deepfake_detector()
