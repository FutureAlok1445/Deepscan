import subprocess, os
def extract_audio_from_video(video: str, out: str) -> bool:
    try:
        subprocess.run(["ffmpeg", "-y", "-i", video, "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1", out], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return os.path.exists(out)
    except Exception: return False