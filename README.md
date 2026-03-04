# DEEP[SCAN] — AI Deepfake Detection Platform

**Team Bug Bytes** | HackHive 2.0 | Cybersecurity PS-03 | Datta Meghe College of Engineering, Airoli

> India's first multi-modal AI deepfake detection engine with rPPG heartbeat analysis, CDCF fusion, and explainable forensic reports in 8 Indian languages.

---

## Team Members

| Name |
|------|
| Alok |
| Rudranarayan Sahu |
| Shubham |
| Raj |

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Frontend** | React 18, Vite 5, Tailwind CSS 3.4, GSAP + ScrollTrigger, Three.js, Recharts, Framer Motion |
| **Backend** | Python 3.x, FastAPI, Uvicorn, Pydantic |
| **AI/ML** | EfficientNet-B4, DistilBERT, librosa, XGBoost, SHAP, Grad-CAM |
| **Physiological** | rPPG (Remote Photoplethysmography) heartbeat detection |
| **Forensics** | ELA, FFT, Noise Analysis, Gabor Filters, EXIF Metadata |
| **Fusion** | CDCF (Cross-Domain Consistency Fusion) Engine |
| **Reports** | ReportLab PDF generation, multi-language narration |
| **Bot** | python-telegram-bot |

---

## AACS Formula

**AI Authenticity Confidence Score:**

```
AACS = ((0.30 × MAS) + (0.25 × PPS) + (0.20 × IRS) + (0.15 × AAS) + (0.10 × CVS)) × CDCF
```

| Sub-Score | Weight | Description |
|-----------|--------|-------------|
| MAS | 0.30 | Media Authenticity Score (CNN-based detection) |
| PPS | 0.25 | Physiological Plausibility Score (rPPG heartbeat) |
| IRS | 0.20 | Information Reliability Score (metadata + news cross-check) |
| AAS | 0.15 | Acoustic Anomaly Score (voice clone detection) |
| CVS | 0.10 | Context Verification Score (reverse image search) |

**Verdict Bands:** 0-30 = Authentic | 31-60 = Uncertain | 61-85 = Likely Fake | 86-100 = Definitely Fake

---

## Quick Start (Local Development)

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.10+
- **Git**

### 1. Clone the Repository

```bash
git clone https://github.com/your-team/deepscan.git
cd deepscan
```

### 2. Start the Backend

```bash
cd backend

# Create a virtual environment (recommended)
python -m venv venv
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start the server
cd ..
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

The backend will be available at:
- **API:** http://localhost:8000
- **Docs (Swagger):** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health

> **Note:** ML packages (torch, transformers, librosa, etc.) are optional. Without them, the system runs with heuristic fallback scores — all API endpoints still work.

### 3. Start the Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The frontend will be available at: **http://localhost:5173** (or next available port)

The Vite dev server proxies API requests to `http://localhost:8000` automatically.

### 4. (Optional) Docker Compose

```bash
docker-compose up --build
```

This starts both backend (port 8000) and frontend (port 3000) in containers.

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze/` | Upload a file for full AACS analysis |
| `POST` | `/api/v1/analyze/url` | Analyze media from a URL |
| `GET` | `/api/v1/history/` | Get analysis history |
| `GET` | `/api/v1/report/{id}` | Download PDF forensic report |
| `GET` | `/api/v1/community/` | Get community-reported deepfakes |
| `POST` | `/api/v1/community/` | Submit a community report |
| `WS` | `/ws/live` | Real-time webcam frame analysis |
| `POST` | `/webhook/telegram` | Telegram bot webhook |
| `GET` | `/health` | Health check |

---

## Project Structure

```
deepscan/
├── backend/
│   ├── main.py                    # FastAPI app entry point
│   ├── config.py                  # Environment settings
│   ├── api/v1/endpoints/          # REST API routes
│   │   ├── analyze.py             # File upload analysis
│   │   ├── analyze_url.py         # URL-based analysis
│   │   ├── history.py             # Analysis history
│   │   ├── report.py              # PDF report download
│   │   ├── community.py           # Community alerts
│   │   ├── live_scan.py           # WebSocket live scan
│   │   └── webhook.py             # Telegram webhook
│   ├── services/
│   │   ├── detection/             # ML detection engines
│   │   │   ├── orchestrator.py    # Central AACS pipeline
│   │   │   ├── image_detector.py  # EfficientNet-B4
│   │   │   ├── video_detector.py  # Multi-frame analysis
│   │   │   ├── audio_detector.py  # MFCC spectral analysis
│   │   │   └── text_detector.py   # DistilBERT NLP
│   │   ├── physiological/         # rPPG heartbeat detection
│   │   ├── forensics/             # ELA, FFT, noise, Gabor, metadata
│   │   ├── fusion/                # CDCF engine + score calculator
│   │   ├── context/               # News cross-check, reverse search
│   │   ├── explainability/        # Grad-CAM, SHAP, LLM narrator
│   │   ├── report/                # PDF report generator
│   │   └── bot/                   # Telegram bot handlers
│   └── utils/                     # File handling, image/audio/video utils
├── frontend/
│   ├── src/
│   │   ├── App.jsx                # Root app with routing
│   │   ├── pages/                 # Home, Analyze, Result, History, Learn, Community
│   │   ├── components/            # UI components (neo-brutalist design)
│   │   └── api/                   # API client with mock fallback
│   ├── package.json
│   └── vite.config.js
├── telegram-bot/                  # Standalone Telegram bot
├── docker-compose.yml
└── README.md
```

---

## Design System

**Neo-Brutalist Cyberpunk:**
- 3px borders, 8px offset flat shadows
- Fonts: Space Grotesk (headings), Space Mono (code/data)
- Colors: `#0a0a0f` (bg), `#ff3c00` (red), `#00f5ff` (cyan), `#39ff14` (green), `#ffd700` (yellow), `#e0e0e0` (silver)

---

## License

Built for HackHive 2.0 Hackathon — Datta Meghe College of Engineering, Airoli
