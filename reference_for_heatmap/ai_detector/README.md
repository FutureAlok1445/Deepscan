# AI Image Detector

Real ML-based AI image detection with ELA heatmap overlay.

## Why a local backend?
Browser-based tools can't call HuggingFace or Anthropic APIs directly due to CORS.
This backend runs on your machine — no CORS, no limits, no cost.

## Setup (one time)

```bash
# 1. Install Python deps
pip install -r requirements.txt

# 2. Start backend (downloads ~500MB model on first run)
cd backend
python main.py
```

## Usage
1. Backend running at http://localhost:8000
2. Open `frontend/index.html` in your browser
3. Upload any image → Analyze

## Models used
- `umm-maybe/AI-image-detector` — general AI detection (DALL-E, SD, MJ, GAN)
- `Organika/sdxl-detector` — Stable Diffusion XL specialist

## How it works
1. Image sent to local FastAPI server
2. HuggingFace transformer model classifies real vs AI
3. ELA (Error Level Analysis) heatmap computed with OpenCV
4. Noise uniformity map computed
5. All signals weighted → final score
6. Thermal heatmap overlaid on original image in browser

## Accuracy
- Much better than client-side heuristics
- Catches fully AI-generated images (Midjourney, SD, DALL-E)
- Catches composites (real photo + AI background)
- Works on photoshopped images via ELA

## API Endpoints
- `POST /detect` — upload image, get score + heatmaps
- `GET /health` — check server + loaded models
