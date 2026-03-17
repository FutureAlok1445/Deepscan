"""
AI Image Detector - FastAPI Backend
====================================
Uses real HuggingFace models locally — no CORS issues.

Install & Run:
  pip install fastapi uvicorn pillow transformers torch torchvision python-multipart
  python main.py

Then open frontend/index.html in your browser.
"""

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import torch
from transformers import pipeline, AutoFeatureExtractor, AutoModelForImageClassification
from PIL import Image
import io
import numpy as np
import base64
import cv2
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Image Detector API", version="1.0.0")

# Allow all origins (frontend running from file:// or localhost)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load models on startup ────────────────────────────────
# Model 1: General AI image detector (trained on DALL-E, SD, MJ, GAN)
MODEL_1 = "umm-maybe/AI-image-detector"
# Model 2: More sensitive deepfake / manipulation detector  
MODEL_2 = "Organika/sdxl-detector"

detectors = {}

@app.on_event("startup")
async def load_models():
    logger.info("Loading AI detection models...")
    try:
        detectors["general"] = pipeline(
            "image-classification",
            model=MODEL_1,
            device=0 if torch.cuda.is_available() else -1
        )
        logger.info(f"✓ Loaded {MODEL_1}")
    except Exception as e:
        logger.error(f"Failed to load model 1: {e}")

    try:
        detectors["sdxl"] = pipeline(
            "image-classification",
            model=MODEL_2,
            device=0 if torch.cuda.is_available() else -1
        )
        logger.info(f"✓ Loaded {MODEL_2}")
    except Exception as e:
        logger.error(f"Failed to load model 2: {e}")

    logger.info("Models ready!")


# ── Main detection endpoint ───────────────────────────────
@app.post("/detect")
async def detect_image(file: UploadFile = File(...)):
    # Read image
    contents = await file.read()
    try:
        img = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(400, "Invalid image file")

    results = {}

    # ── Run ML models ──────────────────────────────────────
    for name, detector in detectors.items():
        try:
            preds = detector(img)
            results[name] = preds
        except Exception as e:
            results[name] = {"error": str(e)}

    # ── Compute ELA heatmap ────────────────────────────────
    ela_b64, ela_score = compute_ela(img)

    # ── Compute noise map ──────────────────────────────────
    noise_b64, noise_score = compute_noise_map(img)

    # ── Parse final AI score ───────────────────────────────
    ai_score = parse_ai_score(results, ela_score, noise_score)

    return JSONResponse({
        "ai_score": ai_score["final"],
        "verdict": ai_score["verdict"],
        "ml_results": results,
        "ela_score": ela_score,
        "noise_score": noise_score,
        "ela_heatmap": ela_b64,       # base64 PNG of ELA map
        "noise_heatmap": noise_b64,   # base64 PNG of noise map
        "signals": ai_score["signals"],
        "image_info": {
            "width": img.width,
            "height": img.height,
            "format": file.content_type,
        }
    })


# ── ELA: Error Level Analysis ─────────────────────────────
def compute_ela(img: Image.Image, quality=65, amplify=14):
    """
    Re-compress image at low quality and amplify the difference.
    High difference = editing seams, AI compositing artifacts.
    """
    # Save at low quality
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=quality)
    buf.seek(0)
    recompressed = Image.open(buf).convert("RGB")

    orig_arr = np.array(img, dtype=np.float32)
    reco_arr = np.array(recompressed, dtype=np.float32)

    diff = np.abs(orig_arr - reco_arr)
    ela_gray = np.mean(diff, axis=2)
    ela_amp = np.clip(ela_gray * amplify, 0, 255).astype(np.uint8)

    # Score = mean anomaly
    score = int(np.mean(ela_amp) / 255 * 100 * 1.6)
    score = min(100, score)

    # Apply thermal colormap
    ela_colored = cv2.applyColorMap(ela_amp, cv2.COLORMAP_JET)
    ela_colored_rgb = cv2.cvtColor(ela_colored, cv2.COLOR_BGR2RGB)
    ela_pil = Image.fromarray(ela_colored_rgb)

    # Encode to base64
    buf2 = io.BytesIO()
    ela_pil.save(buf2, format="PNG")
    b64 = base64.b64encode(buf2.getvalue()).decode()

    return b64, score


# ── Noise Residual Map ─────────────────────────────────────
def compute_noise_map(img: Image.Image):
    """
    High-pass filter: subtract Gaussian blur from original.
    Real cameras: spatially non-uniform noise.
    AI images: unnaturally flat/uniform noise.
    """
    arr = np.array(img.convert("L"), dtype=np.float32)

    # Gaussian blur
    blurred = cv2.GaussianBlur(arr, (5, 5), 0)
    noise = np.abs(arr - blurred)
    noise_amp = np.clip(noise * 7, 0, 255).astype(np.uint8)

    # Score based on spatial uniformity of noise
    # Divide into zones — real photos have MORE variation between zones
    h, w = noise_amp.shape
    zone_means = []
    for zy in range(4):
        for zx in range(4):
            patch = noise_amp[zy*h//4:(zy+1)*h//4, zx*w//4:(zx+1)*w//4]
            zone_means.append(np.mean(patch))

    std_zones = np.std(zone_means)
    mean_noise = np.mean(noise_amp)

    # Low std = uniform noise = AI indicator
    uniformity = max(0, 1 - std_zones / 15)
    score = int(uniformity * 70 + (mean_noise / 255) * 40)
    score = min(100, score)

    # Thermal colormap
    noise_colored = cv2.applyColorMap(noise_amp, cv2.COLORMAP_JET)
    noise_rgb = cv2.cvtColor(noise_colored, cv2.COLOR_BGR2RGB)
    noise_pil = Image.fromarray(noise_rgb)

    buf = io.BytesIO()
    noise_pil.save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return b64, score


# ── Parse & combine scores ─────────────────────────────────
def parse_ai_score(ml_results, ela_score, noise_score):
    ml_score = 50  # default if model fails

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

    # Weighted combination: ML is most reliable
    if ml_results:
        final = int(ml_score * 0.75 + ela_score * 0.15 + noise_score * 0.10)
    else:
        # Fallback to forensics only
        final = int(ela_score * 0.60 + noise_score * 0.40)

    final = max(2, min(97, final))
    verdict = "FAKE" if final > 60 else "PARTIAL" if final > 32 else "REAL"

    signals = [
        {
            "name": "ML Model Detection",
            "score": ml_score,
            "severity": "HIGH" if ml_score > 60 else "MEDIUM" if ml_score > 32 else "LOW",
            "desc": f"Trained classifier score: {ml_score}% AI probability"
        },
        {
            "name": "Error Level Analysis",
            "score": ela_score,
            "severity": "HIGH" if ela_score > 60 else "MEDIUM" if ela_score > 30 else "LOW",
            "desc": "JPEG re-compression inconsistency analysis"
        },
        {
            "name": "Noise Uniformity",
            "score": noise_score,
            "severity": "HIGH" if noise_score > 60 else "MEDIUM" if noise_score > 30 else "LOW",
            "desc": "Spatial noise pattern analysis across image zones"
        },
    ]

    return {"final": final, "verdict": verdict, "signals": signals}


# ── Health check ───────────────────────────────────────────
@app.get("/health")
def health():
    return {
        "status": "ok",
        "models_loaded": list(detectors.keys()),
        "cuda": torch.cuda.is_available()
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)
