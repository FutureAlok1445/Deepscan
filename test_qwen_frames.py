"""
test_qwen_frames.py
───────────────────
Verifies that Qwen VL in LM Studio is actually receiving video
frames and returning visual analysis (not just filename guesses).

Usage:
    python test_qwen_frames.py [path/to/video.mp4]
"""
import sys
import base64
import os
from dotenv import load_dotenv

load_dotenv()

VIDEO_PATH = sys.argv[1] if len(sys.argv) > 1 else "test_videos/ai_video.mp4"
BASE_URL   = os.getenv("LMSTUDIO_BASE_URL", "http://localhost:1234/v1")
MODEL      = os.getenv("LMSTUDIO_MODEL",    "qwen/qwen3.5-9b")

print("=" * 60)
print(f"  Testing Qwen VL frame analysis")
print(f"  Video : {VIDEO_PATH}")
print(f"  URL   : {BASE_URL}")
print(f"  Model : {MODEL}")
print("=" * 60)

# ── Step 1: extract frames ────────────────────────────────────
print("\n[1] Extracting frames with cv2...")
try:
    import cv2
except ImportError:
    print("[FAIL] cv2 not installed. Run: pip install opencv-python")
    sys.exit(1)

cap = cv2.VideoCapture(VIDEO_PATH)
if not cap.isOpened():
    print(f"[FAIL] Could not open: {VIDEO_PATH}")
    sys.exit(1)

total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
fps          = cap.get(cv2.CAP_PROP_FPS)
print(f"       Total frames: {total_frames}, FPS: {fps:.1f}")

frames = []
step   = max(1, total_frames // 8)
for i in range(0, total_frames, step):
    cap.set(cv2.CAP_PROP_POS_FRAMES, i)
    ret, frame = cap.read()
    if ret:
        frames.append(frame)
    if len(frames) >= 8:
        break
cap.release()
print(f"[OK]  Sampled {len(frames)} frames")

# ── Step 2: encode frames as base64 ──────────────────────────
print("\n[2] Encoding frames as base64 JPEG...")
image_contents = []
for idx, f in enumerate(frames):
    _, buf = cv2.imencode('.jpg', f, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
    b64 = base64.b64encode(buf).decode('utf-8')
    kb  = len(buf) / 1024
    image_contents.append({
        "type": "image_url",
        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
    })
    print(f"       Frame {idx+1}: {kb:.1f} KB encoded")
print(f"[OK]  All frames encoded")

# ── Step 3: send to Qwen VL ───────────────────────────────────
print(f"\n[3] Sending {len(frames)} frames to {MODEL}...")
try:
    from openai import OpenAI
except ImportError:
    print("[FAIL] openai not installed. Run: pip install openai")
    sys.exit(1)

client = OpenAI(base_url=BASE_URL, api_key="lm-studio")

prompt_text = (
    "You are a visual forensic analyst. I am sending you video frame samples. "
    "For EACH frame, briefly describe:\n"
    "1. What you can SEE in the frame (people, objects, setting)\n"
    "2. Anything visually suspicious (blurring, artifacts, unnatural lighting)\n\n"
    "If you can see the frames, start with: 'FRAME ANALYSIS:'\n"
    "If you CANNOT see the frames, start with: 'NO VISUAL INPUT RECEIVED'"
)

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": prompt_text},
            *image_contents
        ]
    }
]

try:
    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        max_tokens=800,
        temperature=0.1,
    )
    reply = response.choices[0].message.content.strip()
    print(f"\n{'─'*60}")
    print("RAW RESPONSE FROM QWEN:")
    print(f"{'─'*60}")
    print(reply)
    print(f"{'─'*60}\n")

    if "FRAME ANALYSIS" in reply.upper():
        print("[PASS] ✓ Qwen IS receiving and analyzing visual frames!")
    elif "NO VISUAL INPUT" in reply.upper():
        print("[FAIL] ✗ Qwen says it CANNOT see the frames.")
        print("       → This model may not support vision input.")
        print("       → Load a VL model like Qwen2.5-VL-7B-Instruct in LM Studio.")
    else:
        print("[WARN] ⚠ Response is ambiguous — check manually above.")
        print("       Possible: model is responding but in unexpected format.")

except Exception as e:
    print(f"[FAIL] ✗ API call failed: {e}")
    print("       → Check LM Studio is running and the model is loaded.")
