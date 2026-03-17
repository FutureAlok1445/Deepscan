"""
HeatmapDetector — exact port of reference_for_heatmap/ai_detector/backend/main.py
====================================================================================
Uses the same two HuggingFace models + ELA + noise map pipeline as the reference.

Models:
  - umm-maybe/AI-image-detector   (general AI: DALL-E, SD, MJ, GAN)
  - Organika/sdxl-detector        (SDXL specialist)

Heatmaps:
  - ELA:   JPEG re-compression at quality=65, amplified x14, JET colormap
  - Noise: Gaussian high-pass (5×5), zone uniformity score, JET colormap
"""

import io
import base64
import logging

from loguru import logger

# ── Heavy deps — graceful fallback if missing ──────────────────────────
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    logger.warning("torch not installed — HeatmapDetector ML models disabled")

try:
    from transformers import pipeline as hf_pipeline
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False
    logger.warning("transformers not installed — HeatmapDetector ML models disabled")

try:
    import cv2
    HAS_CV2 = True
except ImportError:
    HAS_CV2 = False
    logger.warning("cv2 not installed — HeatmapDetector will use PIL JET fallback")

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    logger.warning("numpy not installed — HeatmapDetector heatmaps disabled")

from PIL import Image, ImageOps

# ── Model IDs (same as reference) ─────────────────────────────────────
MODEL_GENERAL = "umm-maybe/AI-image-detector"
MODEL_SDXL    = "Organika/sdxl-detector"


class HeatmapDetector:
    """
    Drop-in replacement for the reference ai_detector backend.
    Call `detect(pil_image)` to get the full result dict matching the
    reference `/detect` response shape.
    """

    def __init__(self):
        self._detectors: dict = {}
        self._loaded = False

    # ── Lazy loader ───────────────────────────────────────────────────
    def load_models(self):
        """Load both HF pipelines. Called once at startup or on first use."""
        if self._loaded:
            return
        if not (HAS_TORCH and HAS_TRANSFORMERS):
            logger.warning("HeatmapDetector: torch/transformers unavailable — skipping model load")
            self._loaded = True
            return

        device = 0 if torch.cuda.is_available() else -1
        hf_token = _get_hf_token()

        for name, model_id in [("general", MODEL_GENERAL), ("sdxl", MODEL_SDXL)]:
            try:
                self._detectors[name] = hf_pipeline(
                    "image-classification",
                    model=model_id,
                    device=device,
                    token=hf_token if hf_token else None,
                )
                logger.info(f"HeatmapDetector: loaded {model_id}")
            except Exception as e:
                logger.error(f"HeatmapDetector: failed to load {model_id}: {e}")

        self._loaded = True

    # ── Main detection entry point ────────────────────────────────────
    def detect(self, pil_image: Image.Image) -> dict:
        """
        Run the full reference pipeline on a PIL image.

        Returns a dict matching the reference /detect response:
          {
            ai_score, verdict, ml_results,
            ela_score, noise_score,
            ela_heatmap,   # base64 PNG (JET thermal ELA map)
            noise_heatmap, # base64 PNG (JET thermal noise map)
            signals        # list of signal dicts
          }
        """
        if not self._loaded:
            self.load_models()

        # ── Run ML models ─────────────────────────────────────────────
        ml_results: dict = {}
        for name, detector in self._detectors.items():
            try:
                preds = detector(pil_image)
                ml_results[name] = preds
            except Exception as e:
                ml_results[name] = {"error": str(e)}

        # ── Compute heatmaps ──────────────────────────────────────────
        ela_b64,   ela_score   = compute_ela(pil_image)
        noise_b64, noise_score = compute_noise_map(pil_image)

        # ── Combine into final score ──────────────────────────────────
        ai_score = parse_ai_score(ml_results, ela_score, noise_score)

        return {
            "ai_score":      ai_score["final"],
            "verdict":       ai_score["verdict"],
            "ml_results":    ml_results,
            "ela_score":     ela_score,
            "noise_score":   noise_score,
            "ela_heatmap":   ela_b64,    # raw base64 (no data: prefix)
            "noise_heatmap": noise_b64,  # raw base64 (no data: prefix)
            "signals":       ai_score["signals"],
        }


# ── ELA: Error Level Analysis ─────────────────────────────────────────
def _create_smooth_heatmap(diff_array: np.ndarray) -> Image.Image:
    """Takes a raw absolute difference array and returns a smooth Grad-CAM-like JET PIL image."""
    if not HAS_CV2:
        # Fallback raw amplify if CV2 not present
        raw_amp = np.clip(diff_array * 14, 0, 255).astype(np.uint8)
        return _apply_jet_pil(Image.fromarray(raw_amp))

    h, w = diff_array.shape
    
    # 1. Clean the baseline noise (keep only the top 30% of highest variants)
    p_thresh = np.percentile(diff_array, 70) 
    clean_diff = np.clip(diff_array - p_thresh, 0, None)
    
    # 2. Block dilation to merge scattered noisy pixels into continuous blocks
    dilate_k = int(max(h, w) * 0.015)
    dilate_k = max(3, dilate_k)
    kernel = np.ones((dilate_k, dilate_k), np.uint8)
    dilated = cv2.dilate(clean_diff, kernel, iterations=2)
    
    # 3. Massive Gaussian Blur to smooth out edges (creates the heatblob)
    blur_k = int(max(h, w) * 0.1)
    if blur_k % 2 == 0: 
        blur_k += 1
    blur_k = max(15, blur_k)
    smoothed = cv2.GaussianBlur(dilated, (blur_k, blur_k), sigmaX=blur_k/3.0)
    
    # 4. Normalize dynamically to create vivid hot spots
    smoothed -= np.min(smoothed) # ensure absolute base is dark blue (0)
    max_peak = np.max(smoothed)
    
    # If the anomaly is very faint, we cap the multiplier so it remains safely cool 
    # instead of turning random background noise into bright red.
    multiplier = 255.0 / max_peak if max_peak > 3.0 else 50.0
    multiplier = min(multiplier, 80.0) # hard cap
    
    smooth_amp = np.clip(smoothed * multiplier, 0, 255).astype(np.uint8)
    
    # Apply JET
    colored = cv2.applyColorMap(smooth_amp, cv2.COLORMAP_JET)
    rgb = cv2.cvtColor(colored, cv2.COLOR_BGR2RGB)
    return Image.fromarray(rgb)


def compute_ela(img: Image.Image, quality: int = 65, amplify: int = 14):
    """
    Computes Error Level Analysis and generates a sleek, smoothed heatmap.
    """
    if not HAS_NUMPY:
        return "", 0

    # Re-save at low quality
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    orig_arr = np.array(img, dtype=np.float32)
    reco_arr = np.array(recompressed, dtype=np.float32)

    diff     = np.abs(orig_arr - reco_arr)
    ela_gray = np.mean(diff, axis=2)
    
    # Compute raw score as before for consistency
    ela_raw_amp  = np.clip(ela_gray * amplify, 0, 255).astype(np.uint8)
    score = int(np.mean(ela_raw_amp) / 255 * 100 * 1.6)
    score = min(100, score)

    # ── GENERATE SMOOTH HEATMAP MATCHING REFERENCE ──
    ela_pil = _create_smooth_heatmap(ela_gray)

    buf2 = io.BytesIO()
    ela_pil.save(buf2, format="PNG")
    b64 = base64.b64encode(buf2.getvalue()).decode()
    return b64, score


# ── Noise Residual Map ────────────────────────────────────────────────
def compute_noise_map(img: Image.Image):
    """
    Returns a smooth noise residual heatmap (Gaussian high-pass).
    """
    if not HAS_NUMPY:
        return "", 0

    arr = np.array(img.convert("L"), dtype=np.float32)

    if HAS_CV2:
        blurred = cv2.GaussianBlur(arr, (5, 5), 0)
    else:
        from PIL import ImageFilter
        blurred = np.array(
            img.convert("L").filter(ImageFilter.GaussianBlur(radius=2)),
            dtype=np.float32,
        )

    noise = np.abs(arr - blurred)
    noise_raw_amp = np.clip(noise * 7, 0, 255).astype(np.uint8)

    # Calculate uniform noise score (4×4 zone technique)
    h, w = noise_raw_amp.shape
    zone_means = [
        np.mean(noise_raw_amp[zy * h // 4:(zy + 1) * h // 4,
                              zx * w // 4:(zx + 1) * w // 4])
        for zy in range(4) for zx in range(4)
    ]
    std_zones  = np.std(zone_means)
    mean_noise = np.mean(noise_raw_amp)

    uniformity  = max(0.0, 1.0 - std_zones / 15.0)
    score       = min(100, int(uniformity * 70 + (mean_noise / 255) * 40))

    # ── GENERATE SMOOTH HEATMAP MATCHING REFERENCE ──
    noise_pil = _create_smooth_heatmap(noise)

    buf2 = io.BytesIO()
    noise_pil.save(buf2, format="PNG")
    b64 = base64.b64encode(buf2.getvalue()).decode()
    return b64, score



# ── Score parsing & combination ───────────────────────────────────────
def parse_ai_score(ml_results: dict, ela_score: int, noise_score: int) -> dict:
    """
    Combines ML results and forensics with a 'Suspicious Consistency' penalty.
    Fully artificial images bypass ELA because they are consistently fake.
    We detect this 'over-perfection' and penalize it if ML models give >25%.
    """
    ml_score = 50  # Default if models not loaded

    for model_name, preds in ml_results.items():
        if isinstance(preds, list):
            for p in preds:
                label = p.get("label", "").lower()
                score = p.get("score", 0)
                if any(w in label for w in ["ai", "fake", "artificial", "generated", "synthetic", "diffusion"]):
                    ml_score = int(score * 100)
                    break
                elif any(w in label for w in ["real", "human", "authentic", "natural"]):
                    ml_score = int((1 - score) * 100)
                    break

    # ── Suspicious Consistency Penalty ──────────────────────────────
    # If ELA and Noise are very low (meaning the image is perfectly uniform),
    # but the ML model gives even a moderate AI probability, it's likely a 
    # fully artificial image that bypasses traditional forensics.
    consistency_penalty = 0
    is_suspiciously_uniform = (ela_score < 15 and noise_score < 25)
    
    if is_suspiciously_uniform and ml_score > 25:
        # Bump the score because "Perfect Consistency" is a signature of generative AI
        consistency_penalty = 25
        logger.info(f"Suspicious consistency detected (ELA={ela_score}, Noise={noise_score}). Applying penalty.")

    if ml_results:
        final = int(ml_score * 0.75 + ela_score * 0.15 + noise_score * 0.10) + consistency_penalty
    else:
        # Fallback to forensics only
        final = int(ela_score * 0.60 + noise_score * 0.40)

    final   = max(2, min(97, final))
    verdict = "FAKE" if final > 60 else "PARTIAL" if final > 32 else "REAL"

    signals = [
        {
            "name":     "ML Model Detection",
            "score":    ml_score,
            "severity": "HIGH" if ml_score > 60 else "MEDIUM" if ml_score > 32 else "LOW",
            "desc":     f"Trained classifier score: {ml_score}% AI probability",
        },
        {
            "name":     "Error Level Analysis",
            "score":    ela_score,
            "severity": "HIGH" if ela_score > 60 else "MEDIUM" if ela_score > 30 else "LOW",
            "desc":     "JPEG re-compression inconsistency analysis (quality=65, amplify×14)",
        },
        {
            "name":     "Noise Uniformity",
            "score":    noise_score,
            "severity": "HIGH" if noise_score > 60 else "MEDIUM" if noise_score > 30 else "LOW",
            "desc":     "Spatial noise pattern analysis across 4×4 image zones",
        },
    ]
    
    if consistency_penalty > 0:
        signals.append({
            "name": "Unnatural Consistency",
            "score": 85,
            "severity": "HIGH",
            "desc": "The image is over-perfectly uniform. This is a signature of generative AI (Midjourney/DALL-E) bypassing ELA."
        })

    return {"final": final, "verdict": verdict, "signals": signals}



# ── Helpers ───────────────────────────────────────────────────────────
def _get_hf_token() -> str:
    """Read HF token from config or environment."""
    import os
    # Try config first (loads it)
    try:
        from backend.config import settings
        token = settings.HF_API_TOKEN or settings.HUGGINGFACE_API_KEY or ""
        if token:
            return token
    except Exception:
        pass
    return (
        os.environ.get("HUGGINGFACE_HUB_TOKEN")
        or os.environ.get("HF_API_TOKEN")
        or os.environ.get("HUGGINGFACE_API_KEY")
        or ""
    )


def _apply_jet_pil(gray_img: Image.Image) -> Image.Image:
    """Pure-Python JET colormap fallback (no OpenCV)."""
    rgb = Image.new("RGB", gray_img.size)
    px  = rgb.load()
    gx  = gray_img.load()
    for y in range(gray_img.height):
        for x in range(gray_img.width):
            v = gx[x, y]
            if v < 64:
                r, g, b = 0, v * 4, 255
            elif v < 128:
                r, g, b = 0, 255, 255 - (v - 64) * 4
            elif v < 192:
                r, g, b = (v - 128) * 4, 255, 0
            else:
                r, g, b = 255, 255 - (v - 192) * 4, 0
            px[x, y] = (r, g, b)
    return rgb


# ── Singleton ─────────────────────────────────────────────────────────
heatmap_detector = HeatmapDetector()
