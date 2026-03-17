import numpy as np
import cv2

ela_gray = np.random.uniform(0, 5, (200, 200)).astype(np.float32)
ela_gray[50:100, 50:100] = np.random.uniform(15, 25, (50, 50)).astype(np.float32)

p_thresh = np.percentile(ela_gray, 60)
ela_clean = np.clip(ela_gray - p_thresh, 0, None)

h, w = ela_gray.shape
dilate_k = int(max(h, w) * 0.01)
dilate_k = max(3, dilate_k)
kernel = np.ones((dilate_k, dilate_k), np.uint8)

ela_dilated = cv2.dilate(ela_clean, kernel, iterations=2)

blur_k = int(max(h, w) * 0.1)
if blur_k % 2 == 0: blur_k += 1
blur_k = max(15, blur_k)

smoothed = cv2.GaussianBlur(ela_dilated, (blur_k, blur_k), sigmaX=blur_k/3.0)

max_peak = np.max(smoothed)
print("max peak before mult:", max_peak)
multiplier = 255.0 / max_peak if max_peak > 10 else 25.0
multiplier = min(multiplier, 25.0)
ela_smooth_amp = np.clip(smoothed * multiplier, 0, 255).astype(np.uint8)

print("max amp after mult:", np.max(ela_smooth_amp))
print("min amp after mult:", np.min(ela_smooth_amp))
