import os
import json
from loguru import logger

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False
    logger.warning("anthropic SDK not installed — narration will use fallback")


async def narrate(aacs_score: float, findings: list, language: str = "hi") -> str:
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or not HAS_ANTHROPIC:
        verdict = "authentic" if aacs_score < 30 else "uncertain" if aacs_score < 60 else "likely fake" if aacs_score < 85 else "definitely fake"
        return f"The media scored {aacs_score:.1f}/100 and is classified as {verdict}. {len(findings)} findings were detected. Full AI explanation requires an API key."
    try:
        res = await anthropic.AsyncAnthropic(api_key=key).messages.create(
            max_tokens=256,
            model="claude-3-5-sonnet-20240620",
            system=f"Convert forensics results into 3 simple sentences in {language}.",
            messages=[{"role": "user", "content": json.dumps({"score": aacs_score, "findings": findings})}]
        )
        return res.content[0].text
    except Exception as e:
        logger.debug(f"Narration failed: {e}")
        return f"Analysis complete. AACS Score: {aacs_score:.1f}/100."