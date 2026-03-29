import contextlib
import asyncio
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

try:
    from slowapi.errors import RateLimitExceeded
    from slowapi import _rate_limit_exceeded_handler
    HAS_SLOWAPI = True
except ImportError:
    HAS_SLOWAPI = False

from backend.config import settings
from backend.api.v1.endpoints import (
    analyze, analyze_url, analyze_image, analyze_text, live_scan, history, report, community, webhook, feedback
)
from backend.services.context import deepfake_news_service
from backend.services.detection.orchestrator import orchestrator
from backend.services.IMageDetector.orchestrator import image_orchestrator
from backend.utils.rate_limiter import limiter
from backend.db import models
from backend.db.database import engine


# ═══════════════════════════════════════════════════════════════
# Dependency availability flags (collected at import time)
# ═══════════════════════════════════════════════════════════════
_HAS_TORCH = False
_HAS_TRANSFORMERS = False
_HAS_MEDIAPIPE = False
_HAS_CV2 = False

try:
    import torch
    _HAS_TORCH = True
except ImportError:
    pass
try:
    import transformers
    _HAS_TRANSFORMERS = True
except ImportError:
    pass
try:
    import mediapipe
    _HAS_MEDIAPIPE = True
except ImportError:
    pass
try:
    import cv2
    _HAS_CV2 = True
except ImportError:
    pass


# ═══════════════════════════════════════════════════════════════
# Lifespan: DB init + Model loading + Service validation
# ═══════════════════════════════════════════════════════════════
@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("  DEEP[SCAN] API — Starting up...")
    logger.info("=" * 60)

    # ── Phase 1: Database ──
    try:
        models.Base.metadata.create_all(bind=engine)
        logger.info("[STARTUP] Database tables initialized ✓")
    except Exception as e:
        logger.warning(f"[STARTUP] Database init failed: {e}")

    # ── Phase 2: ML Models ──
    try:
        await orchestrator.load_models()
        await image_orchestrator.load_models()
        logger.info("[STARTUP] ML models loaded ✓")
    except Exception as e:
        logger.warning(f"[STARTUP] Model loading failed (heuristic mode): {e}")

    # ── Phase 3: Service validation ──
    await _validate_services()

    # ── Phase 4: News feed refresh loop ──
    try:
        await deepfake_news_service.start()
        logger.info("[STARTUP] Deepfake news refresh loop started ✓")
    except Exception as e:
        logger.warning(f"[STARTUP] News refresh loop failed to start: {e}")

    yield

    try:
        await deepfake_news_service.stop()
    except Exception:
        pass
    logger.info("Shutting down DeepScan API...")


async def _validate_services():
    """Run startup health checks on all dependencies and services."""
    results = {}

    # Check MongoDB connection
    try:
        from motor.motor_asyncio import AsyncIOMotorClient
        client = AsyncIOMotorClient(settings.MONGO_URI, serverSelectionTimeoutMS=3000)
        await client.admin.command("ping")
        results["mongodb"] = "OK"
        client.close()
    except Exception as e:
        results["mongodb"] = f"UNAVAILABLE — {str(e)[:60]}"

    # Check Redis connection
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_connect_timeout=3)
        await r.ping()
        results["redis"] = "OK"
        await r.close()
    except Exception as e:
        results["redis"] = f"UNAVAILABLE — caching disabled ({str(e)[:40]})"

    # Check ML library availability
    results["torch"] = f"OK (v{torch.__version__})" if _HAS_TORCH else "UNAVAILABLE — heuristic mode"
    results["transformers"] = "OK" if _HAS_TRANSFORMERS else "UNAVAILABLE — HF models disabled"
    results["mediapipe"] = "OK" if _HAS_MEDIAPIPE else "UNAVAILABLE — rPPG/face mesh disabled"
    results["opencv"] = f"OK (v{cv2.__version__})" if _HAS_CV2 else "UNAVAILABLE — video analysis degraded"

    # Check API keys
    results["huggingface_key"] = "OK" if settings.HF_API_TOKEN and not settings.HF_API_TOKEN.startswith("hf_...") else "NOT SET"
    results["groq_key"] = "OK" if settings.GROQ_API_KEY and not settings.GROQ_API_KEY.startswith("gsk_...") else "NOT SET"
    results["news_api_key"] = "OK" if settings.NEWS_API_KEY else "NOT SET"

    # Log everything clearly
    logger.info("─" * 50)
    logger.info("  SERVICE HEALTH CHECK")
    logger.info("─" * 50)
    for service, status in results.items():
        if "UNAVAILABLE" in str(status) or "NOT SET" in str(status) or "FAILED" in str(status):
            logger.warning(f"  ⚠ {service:20s} → {status}")
        else:
            logger.info(f"  ✓ {service:20s} → {status}")
    logger.info("─" * 50)

    mode = "FULL ML" if _HAS_TORCH and _HAS_TRANSFORMERS else "HEURISTIC FALLBACK"
    logger.info(f"  DEEP[SCAN] ready. Mode: {mode}")
    logger.info("=" * 60)


# ═══════════════════════════════════════════════════════════════
# App & Middleware
# ═══════════════════════════════════════════════════════════════
app = FastAPI(
    title="DeepScan API",
    version="1.0.0",
    description="Multi-modal deepfake detection platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

# Register SlowAPI rate limiter
app.state.limiter = limiter
if HAS_SLOWAPI:
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    # Relaxed CSP for hackathon demo — tighten in production
    response.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' blob: data: *"
    return response

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=200,  # NEVER 500 during demo
        content={
            "status": "error",
            "aacs_score": 50.0,
            "verdict": "Uncertain",
            "detail": f"Internal error: {str(exc)[:200]}",
        }
    )

# ═══════════════════════════════════════════════════════════════
# Routes
# ═══════════════════════════════════════════════════════════════
app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analyze"])
app.include_router(analyze_url.router, prefix="/api/v1/analyze", tags=["Analyze URL"])
app.include_router(analyze_image.router, prefix="/api/v1/analyze", tags=["Analyze Image"])
app.include_router(analyze_text.router, prefix="/api/v1/analyze/text", tags=["Analyze Text"])
app.include_router(live_scan.router, prefix="/api/v1/live", tags=["Live Scan"])
app.include_router(history.router, prefix="/api/v1/history", tags=["History"])
app.include_router(report.router, prefix="/api/v1/report", tags=["Report"])
app.include_router(community.router, prefix="/api/v1/community", tags=["Community"])
app.include_router(feedback.router, prefix="/api/v1/feedback", tags=["Feedback"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "service": "DeepScan API",
        "version": "1.0.0",
        "mode": "FULL ML" if _HAS_TORCH else "HEURISTIC FALLBACK",
        "torch": _HAS_TORCH,
        "opencv": _HAS_CV2,
        "mediapipe": _HAS_MEDIAPIPE,
    }