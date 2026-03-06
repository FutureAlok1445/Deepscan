"""
Generate 3 synthetic test videos for detection accuracy testing:
1. real_video.mp4  - mimics real camera: natural noise, irregular motion, PRNU
2. ai_video.mp4    - mimics AI-generated: smooth, no noise, uniform, perfect motion
3. slight_ai.mp4   - in between: mostly natural but with AI-like smoothness regions
"""
import cv2
import numpy as np
import os

OUT_DIR = "test_videos"
os.makedirs(OUT_DIR, exist_ok=True)

W, H, FPS, FRAMES = 320, 240, 15, 45  # 3 seconds each

def make_writer(name):
    path = os.path.join(OUT_DIR, name)
    out = cv2.VideoWriter(path, cv2.VideoWriter_fourcc(*'mp4v'), FPS, (W, H))
    return out, path

# ── 1. REAL VIDEO ──────────────────────────────────────────────────────────────
# Characteristics: natural PRNU (per-pixel fixed pattern noise), irregular
#                  hand-shake motion, organic colour shift, varied brightness
print("Generating real_video.mp4...")
writer, path = make_writer("real_video.mp4")
prnu = (np.random.randn(H, W, 3) * 4).astype(np.float32)  # sensor fingerprint

for i in range(FRAMES):
    # Organic gradient that slowly drifts (natural lighting change)
    t = i / FRAMES
    base_r = int(80 + 40*np.sin(2*np.pi*t))
    base_g = int(60 + 30*np.sin(2*np.pi*t + 1.2))
    base_b = int(70 + 35*np.sin(2*np.pi*t + 2.4))

    frame = np.zeros((H, W, 3), np.float32)
    # Gradient across frame (non-uniform, organic)
    for c, base in enumerate([base_b, base_g, base_r]):
        frame[:, :, c] = base + np.linspace(-20, 20, W)[np.newaxis, :]
        frame[:, :, c] += np.linspace(-10, 10, H)[:, np.newaxis]

    # Add PRNU (fixed camera sensor noise — unique fingerprint)
    frame += prnu
    # Add random temporal noise (shot noise)
    frame += np.random.randn(H, W, 3) * 6
    # Hand-shake: small random sub-pixel translation
    dx, dy = np.random.randint(-3, 4), np.random.randint(-3, 4)
    M = np.float32([[1, 0, dx], [0, 1, dy]])
    frame = cv2.warpAffine(frame, M, (W, H))

    frame = np.clip(frame, 0, 255).astype(np.uint8)
    writer.write(frame)
writer.release()
print(f"  -> {path}")

# ── 2. AI-GENERATED VIDEO ─────────────────────────────────────────────────────
# Characteristics: perfectly smooth motion, zero noise, uniform gradients,
#                  no PRNU, impossible velocity changes every few frames
print("Generating ai_video.mp4...")
writer, path = make_writer("ai_video.mp4")

for i in range(FRAMES):
    t = i / FRAMES
    frame = np.zeros((H, W, 3), np.uint8)
    # Perfectly uniform gradient — no noise at all (AI diffusion artifact)
    val_r = int(128 + 100 * np.sin(2 * np.pi * t))
    val_g = int(128 + 100 * np.cos(2 * np.pi * t))
    val_b = int(200)
    frame[:, :, 0] = val_b
    frame[:, :, 1] = val_g
    frame[:, :, 2] = val_r

    # Add extremely smooth spatial gradient (diffusion model hallmark)
    grad = np.linspace(0, 40, W, dtype=np.uint8)
    frame[:, :, 0] = np.clip(frame[:, :, 0].astype(int) + grad[np.newaxis, :], 0, 255).astype(np.uint8)

    # Impossible velocity: jump to completely different position every 5 frames
    if i % 5 == 0 and i > 0:
        jump = np.random.randint(30, 60)
        frame = np.roll(frame, jump, axis=1)  # teleport — impossible physics

    writer.write(frame)
writer.release()
print(f"  -> {path}")

# ── 3. SLIGHTLY AI VIDEO ──────────────────────────────────────────────────────
# Characteristics: mostly real-looking, but with occasional smooth patches
#                  and slightly-too-perfect local regions
print("Generating slight_ai.mp4...")
writer, path = make_writer("slight_ai.mp4")
prnu2 = (np.random.randn(H, W, 3) * 2).astype(np.float32)  # weaker fingerprint

for i in range(FRAMES):
    t = i / FRAMES
    frame = np.zeros((H, W, 3), np.float32)
    # Mix of natural gradient + AI smoothing in the centre
    for c in range(3):
        base = 80 + 30 * np.sin(2*np.pi*t + c)
        frame[:, :, c] = base
        frame[:, :, c] += np.random.randn(H, W) * 3  # some noise

    # Centre 1/3 is suspiciously smooth (AI touch-up zone)
    cx_s, cx_e = W//3, 2*W//3
    for c in range(3):
        frame[:, cx_s:cx_e, c] = frame[:, cx_s:cx_e, c].mean()  # flat = AI

    frame += prnu2  # weak PRNU — not totally natural
    # Small but non-random motion (slightly too regular)
    dx = int(2 * np.sin(2 * np.pi * i / 20))
    M = np.float32([[1, 0, dx], [0, 1, 0]])
    frame = cv2.warpAffine(frame, M, (W, H))

    frame = np.clip(frame, 0, 255).astype(np.uint8)
    writer.write(frame)
writer.release()
print(f"  -> {path}")

print("\nAll test videos generated in ./test_videos/")
