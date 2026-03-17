import os
import json
import httpx
from loguru import logger


async def narrate(aacs_score: float, findings: list, language: str = "hi") -> str:
    """Generate a human-readable narration of the analysis results using Groq LLM."""
    key = os.getenv("GROQ_API_KEY", "")
    if not key:
        verdict = "authentic" if aacs_score < 30 else "uncertain" if aacs_score < 60 else "likely fake" if aacs_score < 85 else "definitely fake"
        return f"The media scored {aacs_score:.1f}/100 and is classified as {verdict}. {len(findings)} findings were detected."

    lang_map = {"hi": "Hindi (Hinglish)", "en": "English", "bn": "Bengali", "ta": "Tamil"}
    lang_name = lang_map.get(language, "English")

    prompt = (
        f"You are DeepScan AI, a deepfake forensics expert. "
        f"Summarize these detection results in 3 simple sentences in {lang_name}. "
        f"Be direct and clear about whether the media appears real or fake. "
        f"Crucially, the AACS score represents Fake Probability: "
        f"Low scores (0-30) are REAL/AUTHENTIC, medium scores (31-60) are UNCERTAIN, and high scores (61-100) are FAKE/SYNTHETIC.\n\n"
        f"AACS Score: {aacs_score:.1f}/100\n"
        f"Findings: {json.dumps(findings[:5])}"
    )

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 256,
                    "temperature": 0.7,
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.warning(f"Groq API error ({response.status_code}): {response.text}")
                return f"Analysis complete. AACS Score: {aacs_score:.1f}/100."
    except Exception as e:
        logger.debug(f"Narration failed: {e}")
        return f"Analysis complete. AACS Score: {aacs_score:.1f}/100."