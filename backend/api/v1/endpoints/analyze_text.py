"""
Text analysis endpoint — detect AI-generated text (GPT, Claude, Gemini, etc.)
"""
import time
import uuid
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from loguru import logger
from backend.utils.rate_limiter import limiter
from backend.services.detection.text_detector import TextDetector
from backend.services.fusion.score_calculator import get_verdict, get_verdict_color

router = APIRouter()
text_detector = TextDetector()

# In-memory store (shared with analyze.py via import)
text_results_store: dict = {}


class TextAnalyzeRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=50000, description="Text to analyze")
    language: str = Field(default="en", description="Language code")


@router.post("")
@limiter.limit("20/minute")
async def analyze_text(request: Request, body: TextAnalyzeRequest):
    """Analyze text to detect if it was AI-generated."""
    start = time.time()
    analysis_id = f"txt-{uuid.uuid4().hex[:12]}"
    text = body.text.strip()
    word_count = len(text.split())

    if word_count < 5:
        raise HTTPException(status_code=400, detail="Text must be at least 5 words long")

    logger.info(f"[{analysis_id}] Text analysis — {word_count} words")

    try:
        ai_score = await text_detector.analyze(text)

        # Heuristic boosters for very short / very repetitive text
        # Short text is harder to classify — reduce confidence
        if word_count < 20:
            ai_score = ai_score * 0.7  # dampen confidence for short text

        ai_score = max(0.0, min(100.0, ai_score))
        verdict = get_verdict(ai_score)
        elapsed = round(time.time() - start, 3)

        # Build sentence-level breakdown
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]
        sentence_scores = []
        for sent in sentences[:20]:  # max 20 sentences to keep it fast
            if len(sent.split()) >= 3:
                try:
                    s_score = await text_detector.analyze(sent)
                    sentence_scores.append({
                        "text": sent[:200],
                        "ai_probability": round(s_score, 1),
                        "label": "AI" if s_score >= 60 else "Human" if s_score < 30 else "Mixed",
                    })
                except Exception:
                    sentence_scores.append({"text": sent[:200], "ai_probability": 50.0, "label": "Unknown"})

        result = {
            "id": analysis_id,
            "type": "text",
            "score": round(ai_score, 1),
            "aacs_score": round(ai_score, 1),
            "verdict": verdict,
            "verdict_color": get_verdict_color(verdict),
            "word_count": word_count,
            "sentence_count": len(sentences),
            "sentence_scores": sentence_scores,
            "processing_time_ms": round(elapsed * 1000),
            "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "findings": [
                {
                    "engine": "AI-Text-Detector",
                    "score": round(ai_score, 1),
                    "detail": f"HuggingFace desklib/ai-text-detector-v1.01 — {verdict} ({round(ai_score, 1)}%)",
                },
                {
                    "engine": "TextStats",
                    "score": round(ai_score, 1),
                    "detail": f"Analyzed {word_count} words across {len(sentences)} sentences",
                },
            ],
            "narrative": {
                "summary": _build_narrative(ai_score, word_count, verdict),
                "eli5": _build_eli5(ai_score, verdict),
            },
        }

        text_results_store[analysis_id] = result
        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Text analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Text analysis failed: {str(e)}")


def _build_narrative(score, word_count, verdict):
    if score >= 70:
        return f"This text ({word_count} words) shows strong indicators of AI generation. Writing style, vocabulary patterns, and sentence structure are consistent with large language model output."
    elif score >= 40:
        return f"This text ({word_count} words) has mixed signals. Some patterns resemble AI-generated content, but others appear human-written. It may be AI-assisted or heavily edited AI output."
    else:
        return f"This text ({word_count} words) appears to be human-written. Natural language patterns, varied sentence structure, and organic vocabulary suggest authentic human authorship."


def _build_eli5(score, verdict):
    if score >= 70:
        return "This text was probably written by an AI like ChatGPT or Claude. It has that 'too perfect' quality that AI writing often has."
    elif score >= 40:
        return "We're not sure — this text could be written by a human who writes very neatly, or by an AI. It's somewhere in between."
    else:
        return "This looks like it was written by a real person. The writing style feels natural and human."
