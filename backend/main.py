import contextlib
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
    analyze, analyze_url, live_scan, history, report, community, webhook
)
from backend.services.detection.orchestrator import orchestrator
from backend.utils.rate_limiter import limiter

@contextlib.asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting DeepScan API — loading models...")
    try:
        await orchestrator.load_models()
        logger.info("All ML models loaded successfully")
    except Exception as e:
        logger.warning(f"Model preload failed (will lazy-load): {e}")
    yield
    logger.info("Shutting down DeepScan API...")

app = FastAPI(
    title="DeepScan API",
    version="1.0.0",
    description="Multi-modal deepfake detection platform",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    return JSONResponse(status_code=500, content={"detail": "Internal server error."})

app.include_router(analyze.router, prefix="/api/v1/analyze", tags=["Analyze"])
app.include_router(analyze_url.router, prefix="/api/v1/analyze", tags=["Analyze URL"])
app.include_router(live_scan.router, prefix="/ws", tags=["Live Scan"])
app.include_router(history.router, prefix="/api/v1/history", tags=["History"])
app.include_router(report.router, prefix="/api/v1/report", tags=["Report"])
app.include_router(community.router, prefix="/api/v1/community", tags=["Community"])
app.include_router(webhook.router, prefix="/webhook", tags=["Webhook"])

@app.get("/health", tags=["Health"])
async def health_check():
    return {"status": "ok", "service": "DeepScan API", "version": "1.0.0"}