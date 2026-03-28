"""
VideoDescriber — sends sampled video frames to Qwen VL (LM Studio) for
expert deepfake analysis. Returns the raw, unformatted AI response.

Key design decisions:
  • Only 3 frames are sent — LM Studio's Qwen VL endpoint becomes
    unstable above ~4 concurrent images in one request (400 errors).
  • Images are validated + resized to 512 px wide before encoding to keep
    the request payload small.
  • The blocking HTTP call is offloaded to asyncio.to_thread so FastAPI
    stays responsive.
  • If LM Studio returns a 400 we retry up to MAX_RETRIES times with
    exponential back-off, reducing the frame count on each retry.
  • No Groq / text-only fallback — if Qwen cannot be reached the frontend
    receives a clear 'unavailable' message.
"""

import asyncio
import base64
import time
import re

import cv2
import numpy as np
from loguru import logger
from backend.config import settings


# ── Tune these if your LM Studio instance is faster/slower ────────────────────
MAX_FRAMES   = 3      # frames per Qwen call  (keep ≤ 4 for LM Studio stability)
MAX_WIDTH    = 512    # px — smaller = more stable + faster
JPEG_QUALITY = 80
MAX_RETRIES  = 3      # retry attempts if LM Studio returns 400
RETRY_DELAY  = 5.0    # seconds between retries
# ──────────────────────────────────────────────────────────────────────────────


class VideoDescriber:

    def __init__(self):
        self.client = None
        self.model  = None
        self._connect()

    def _connect(self):
        """Initialise the OpenAI-compatible client pointing at LM Studio."""
        try:
            from openai import OpenAI
            client = OpenAI(
                base_url=settings.LMSTUDIO_BASE_URL,
                api_key="lm-studio",
                timeout=300,        # LM Studio can be slow on first token
            )
            # Quick connectivity check
            available = [m.id for m in client.models.list().data]
            model = settings.LMSTUDIO_MODEL

            if available and model not in available:
                logger.warning(
                    f"[VideoDescriber] Warning: '{model}' not in {available}. "
                    "Ensure the correct model is loaded in LM Studio."
                )
            else:
                logger.info(
                    f"[VideoDescriber] Connected — model: {model} | "
                    f"LM Studio: {settings.LMSTUDIO_BASE_URL}"
                )

            self.client = client
            self.model  = model

        except Exception as e:
            logger.warning(f"[VideoDescriber] Cannot connect to LM Studio: {e}")

    # ── public ─────────────────────────────────────────────────────────────────

    async def describe(self, frames: list, filename: str = "video") -> dict:
        """
        Main entry point — analyse sampled frames with Qwen VL.
        Returns a dict with `description` (raw AI text) and `raw_mode=True`.
        """
        if not self.client:
            logger.warning("[VideoDescriber] No LM Studio connection — skipping.")
            return _unavailable()

        if not frames:
            logger.warning("[VideoDescriber] No frames provided.")
            return _unavailable()

        # ── 1. Sample & encode frames ─────────────────────────────────────────
        image_parts = _sample_and_encode(frames, MAX_FRAMES, MAX_WIDTH, JPEG_QUALITY)
        if not image_parts:
            logger.warning("[VideoDescriber] All frames failed to encode — skipping.")
            return _unavailable()

        logger.info(
            f"[VideoDescriber] Prepared {len(image_parts)} frame(s) for '{filename}'"
        )

        # ── 2. Build the analyst prompt ───────────────────────────────────────
        prompt = _build_prompt(filename, len(image_parts))

        # ── 3. Call Qwen with retry logic ─────────────────────────────────────
        frames_to_send = image_parts
        last_error     = None

        for attempt in range(1, MAX_RETRIES + 1):
            logger.info(
                f"[VideoDescriber] Attempt {attempt}/{MAX_RETRIES} — "
                f"sending {len(frames_to_send)} image(s) to Qwen…"
            )
            try:
                raw_text = await _call_qwen(
                    self.client, self.model, prompt, frames_to_send
                )
                logger.success(
                    f"[VideoDescriber] Got {len(raw_text)}-char response on attempt {attempt}."
                )
                return _build_result(raw_text)

            except Exception as e:
                last_error = e
                err_str    = str(e)

                # 400 "failed to process image" → reduce frame count + wait
                if "400" in err_str and "process image" in err_str.lower():
                    if len(frames_to_send) > 1:
                        frames_to_send = frames_to_send[:len(frames_to_send) - 1]
                        logger.warning(
                            f"[VideoDescriber] 400 image-processing error. "
                            f"Reducing to {len(frames_to_send)} frame(s) and retrying in "
                            f"{RETRY_DELAY}s…"
                        )
                    else:
                        logger.error(
                            "[VideoDescriber] 400 persists even with a single frame — "
                            "LM Studio may be overloaded or the model doesn't support vision."
                        )
                        break
                else:
                    logger.error(f"[VideoDescriber] Unexpected error: {e}")
                    break

                await asyncio.sleep(RETRY_DELAY)

        logger.error(f"[VideoDescriber] All attempts exhausted. Last error: {last_error}")
        return _unavailable()


# ── module-level helpers (no `self` needed) ────────────────────────────────────

def _sample_and_encode(
    frames: list, max_frames: int, max_width: int, jpeg_quality: int
) -> list:
    """Sample `max_frames` evenly from `frames`, resize and base64-encode each."""
    total  = len(frames)
    step   = max(1, total // max_frames)
    sample = frames[::step][:max_frames]

    parts = []
    for idx, bgr in enumerate(sample):
        try:
            if bgr is None or not isinstance(bgr, np.ndarray) or bgr.size == 0:
                logger.debug(f"[VideoDescriber] Frame {idx} is empty — skipping")
                continue

            h, w = bgr.shape[:2]
            if w > max_width:
                scale = max_width / w
                bgr   = cv2.resize(
                    bgr,
                    (max_width, int(h * scale)),
                    interpolation=cv2.INTER_AREA,
                )

            ok, buf = cv2.imencode(
                ".jpg", bgr,
                [int(cv2.IMWRITE_JPEG_QUALITY), jpeg_quality]
            )
            if not ok or buf is None or len(buf) == 0:
                logger.debug(f"[VideoDescriber] Frame {idx} encode failed — skipping")
                continue

            b64 = base64.b64encode(buf.tobytes()).decode("utf-8")
            parts.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{b64}"},
            })

        except Exception as e:
            logger.debug(f"[VideoDescriber] Frame {idx} error: {e} — skipping")

    return parts


def _build_prompt(filename: str, num_frames: int) -> str:
    return (
        f"You are an elite forensic deepfake analyst. You have been given {num_frames} frame(s) "
        f"extracted at even intervals from the video file '{filename}'. "
        "Perform a comprehensive, expert-level deepfake and media-manipulation investigation.\n\n"
        "Examine every forensic dimension visible in the frames:\n"
        "  • Face boundary integrity — blending seams, colour discontinuities, soft-edge artefacts\n"
        "  • Skin texture — waxy, over-smooth, or inconsistent rendering between frames\n"
        "  • Eye physiology — specular highlights, iris coherence, reflections, asymmetry\n"
        "  • Lips & teeth — mechanical movement, UV mismatch, mouth boundary flicker\n"
        "  • Temporal stability — glitching, warping, feature popping between frames\n"
        "  • Hair & ear rendering — physics plausibility, integration with background\n"
        "  • Background behaviour — pixel-perfect stability while the subject moves (GAN hallmark)\n"
        "  • Lighting & shadow physics — direction consistency, cast shadow naturalness\n"
        "  • Compression fingerprints — JPEG block artefacts in face vs. background\n"
        "  • Subject identity — identify any recognisable public figures and their role\n"
        "  • Narrative intent — what is this video designed to convey or induce?\n"
        "  • Disinformation risk — rate LOW / MEDIUM / HIGH / CRITICAL and justify\n\n"
        "Write your full analysis in fluent expert prose. Do NOT use rigid section headers or bullet "
        "templates — write as a senior analyst submitting their findings report. Be specific: "
        "reference the frame index, describe artefact locations, and state your confidence level.\n\n"
        "Conclude with your final verdict — AUTHENTIC, SUSPICIOUS, LIKELY SYNTHETIC, or "
        "CONFIRMED SYNTHETIC — and cite the two strongest pieces of forensic evidence."
    )


async def _call_qwen(client, model: str, prompt: str, image_parts: list) -> str:
    """
    Fire the actual LM Studio API request on a background thread and return
    the raw response text.  Raises on any HTTP error so callers can retry.
    """
    messages = [{
        "role": "user",
        "content": [{"type": "text", "text": prompt}] + image_parts,
    }]

    # Run blocking OpenAI SDK call in a thread pool so asyncio event loop
    # stays free during the (potentially multi-minute) LM Studio generation.
    def _sync_call():
        return client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=1400,
            temperature=0.15,
        )

    response = await asyncio.to_thread(_sync_call)
    return response.choices[0].message.content.strip()


def _build_result(raw_text: str) -> dict:
    verdict = _extract_verdict(raw_text)
    return {
        "description":    raw_text,
        "raw_mode":       True,
        "verdict":        verdict,
        "verdict_detail": "",
        "setting":        "Unknown",
        "people":         "Unknown",
        "activity":       "Unknown",
        "artifacts":      [],
        "moments":        [],
        "context":        raw_text,
    }


def _extract_verdict(text: str) -> str:
    patterns = [
        (r"\bCONFIRMED\s+SYNTHETIC\b", "DEFINITE_AI"),
        (r"\bDEFINITE_AI\b",            "DEFINITE_AI"),
        (r"\bLIKELY\s+SYNTHETIC\b",     "LIKELY_AI"),
        (r"\bLIKELY_AI\b",              "LIKELY_AI"),
        (r"\bSUSPICIOUS\b",             "SUSPICIOUS"),
        (r"\bAUTHENTIC\b",              "CLEAN"),
        (r"\bCLEAN\b",                  "CLEAN"),
        (r"\bdeepfake\b",               "LIKELY_AI"),
        (r"\bsynthetic\b",              "LIKELY_AI"),
        (r"\bmanipulated\b",            "SUSPICIOUS"),
    ]
    for pattern, verdict in patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return verdict
    return "UNKNOWN"


def _unavailable() -> dict:
    return {
        "description":    (
            "Visual forensic analysis unavailable — "
            "LM Studio / Qwen VL could not process the video frames."
        ),
        "raw_mode":       True,
        "verdict":        "UNKNOWN",
        "verdict_detail": "",
        "setting":        "N/A",
        "people":         "N/A",
        "activity":       "N/A",
        "artifacts":      [],
        "moments":        [],
        "context":        "N/A",
    }
