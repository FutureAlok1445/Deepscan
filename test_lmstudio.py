"""
Quick test to verify LM Studio is reachable and Qwen model is loaded.
Run from the project root:  python test_lmstudio.py
"""
import sys
import base64
import numpy as np

LM_URL = "http://127.0.0.1:1234/v1"

try:
    from openai import OpenAI
    client = OpenAI(base_url=LM_URL, api_key="lm-studio")
except ImportError:
    print("[ERROR] openai package not installed. Run: pip install openai")
    sys.exit(1)

print(f"\n{'='*60}")
print(f"Testing LM Studio at {LM_URL}")
print(f"{'='*60}\n")

# Step 1: Connectivity
print("[1] Checking LM Studio availability...")
try:
    model_list = client.models.list()
    models = [m.id for m in model_list.data]
    if not models:
        print("[FAIL] LM Studio is running but NO MODEL is loaded!")
        print("       → Open LM Studio → Models → Load a model (e.g., Qwen2.5-VL)")
        sys.exit(1)
    print(f"[OK]  Connected. Loaded models: {models}")
    model_id = models[0]
    print(f"[OK]  Will use model: {model_id}")
except Exception as e:
    print(f"[FAIL] Cannot connect to LM Studio: {e}")
    print(f"       → Make sure LM Studio is running and 'Start Server' is clicked")
    sys.exit(1)

# Step 2: Text-only chat
print("\n[2] Testing text-only chat...")
try:
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": "Reply with exactly: LMSTUDIO_OK"}],
        max_tokens=20,
        temperature=0.0,
    )
    reply = resp.choices[0].message.content.strip()
    print(f"[OK]  Model responded: '{reply}'")
except Exception as e:
    print(f"[FAIL] Text chat failed: {e}")
    sys.exit(1)

# Step 3: Vision (multimodal) test with a tiny synthetic image
print("\n[3] Testing vision/multimodal capability...")
try:
    # Create a small 64x64 red square as test "frame"
    img = np.zeros((64, 64, 3), dtype=np.uint8)
    img[:, :] = [0, 0, 200]  # red
    import cv2
    _, buf = cv2.imencode('.jpg', img)
    b64 = base64.b64encode(buf).decode()

    resp = client.chat.completions.create(
        model=model_id,
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": "What color is the dominant color in this image? Reply in one word."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]
        }],
        max_tokens=10,
        temperature=0.0,
    )
    vision_reply = resp.choices[0].message.content.strip()
    print(f"[OK]  Vision test passed. Model says: '{vision_reply}'")
except Exception as e:
    print(f"[WARN] Vision test failed (model may be text-only): {e}")
    print("       → Ensure you have loaded a VL (Vision-Language) model e.g. Qwen2.5-VL")

print(f"\n{'='*60}")
print("LM Studio is ready for DeepScan video analysis!")
print(f"Model in use: {model_id}")
print(f"\nUpdate backend/config.py LMSTUDIO_MODEL to: \"{model_id}\"")
print(f"{'='*60}\n")
