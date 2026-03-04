import os
import uuid
import tempfile
import httpx
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from loguru import logger
from backend.utils.rate_limiter import limiter
from backend.services.detection.orchestrator import orchestrator
from backend.services.context.url_scraper import UrlScraper
from backend.api.v1.endpoints.analyze import results_store

router = APIRouter()
url_scraper = UrlScraper()


class UrlAnalyzeRequest(BaseModel):
    url: str


@router.post("/url")
@limiter.limit("10/minute")
async def analyze_by_url(request: Request, payload: UrlAnalyzeRequest):
    """Download media from a URL and run the full AACS pipeline."""
    logger.info(f"Scanning URL: {payload.url}")

    # Try to download the file directly first
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(payload.url, timeout=30.0)
            resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        ext = "jpg"
        if "png" in content_type:
            ext = "png"
        elif "mp4" in content_type or "video" in content_type:
            ext = "mp4"
        elif "wav" in content_type or "audio" in content_type:
            ext = "wav"
        elif "mp3" in content_type:
            ext = "mp3"

        # Save to temp
        _upload_dir = os.path.join(tempfile.gettempdir(), "deepscan_uploads")
        fname = os.path.join(_upload_dir, f"url_{uuid.uuid4().hex}.{ext}")
        os.makedirs(_upload_dir, exist_ok=True)
        with open(fname, "wb") as f:
            f.write(resp.content)

        result = await orchestrator.process_media(fname, content_type)
        result["source_url"] = payload.url
        results_store[result["id"]] = result

        # Cleanup
        try:
            os.remove(fname)
        except Exception:
            pass

        return JSONResponse(content=result)
    except httpx.HTTPError as e:
        logger.warning(f"Direct download failed, trying scraper: {e}")

    # Fallback: scrape page for media
    try:
        media_urls = await url_scraper.extract_media(payload.url)
        if not media_urls:
            raise HTTPException(status_code=400, detail="No media found at the given URL")

        # Analyze first image found
        first_url = media_urls[0]
        if first_url.startswith("//"):
            first_url = "https:" + first_url
        elif first_url.startswith("/"):
            from urllib.parse import urlparse
            parsed = urlparse(payload.url)
            first_url = f"{parsed.scheme}://{parsed.netloc}{first_url}"

        async with httpx.AsyncClient(follow_redirects=True) as client:
            resp = await client.get(first_url, timeout=30.0)
            resp.raise_for_status()

        _upload_dir2 = os.path.join(tempfile.gettempdir(), "deepscan_uploads")
        fname = os.path.join(_upload_dir2, f"scraped_{uuid.uuid4().hex}.jpg")
        os.makedirs(_upload_dir2, exist_ok=True)
        with open(fname, "wb") as f:
            f.write(resp.content)

        result = await orchestrator.process_media(fname, "image/jpeg")
        result["source_url"] = payload.url
        result["scraped_from"] = first_url
        results_store[result["id"]] = result

        try:
            os.remove(fname)
        except Exception:
            pass

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"URL analysis failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to analyze URL")