import httpx
from loguru import logger


class NewsCrossChecker:
    """Cross-check media context against known news sources.

    Uses a heuristic approach: checks if the content can be corroborated
    by credible news outlets. In production, integrate with NewsAPI or
    Google Fact Check Tools API.
    """

    FACT_CHECK_SOURCES = [
        "factcheck.org",
        "snopes.com",
        "altnews.in",
        "boomlive.in",
        "vishvasnews.com",
    ]

    def verify_event(self, context_text: str) -> bool:
        """Return True if content appears credible, False if suspicious."""
        if not context_text or context_text.startswith("file:"):
            # File-based analysis — no textual context to verify
            return True

        # Simple heuristic checks for deepfake indicators
        suspicious_phrases = [
            "breaking:", "leaked:", "shocking:", "you won't believe",
            "share before deleted", "viral video proves",
            "secret recording", "banned video",
        ]

        text_lower = context_text.lower()
        suspicion_count = sum(1 for phrase in suspicious_phrases if phrase in text_lower)

        if suspicion_count >= 2:
            logger.info(f"News cross-check: {suspicion_count} suspicious phrases found")
            return False

        return True

    async def verify_with_api(self, claim: str) -> dict:
        """Attempt to verify a claim using Google Fact Check Tools API."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://factchecktools.googleapis.com/v1alpha1/claims:search",
                    params={"query": claim[:200], "languageCode": "en"},
                    timeout=10.0,
                )
                if resp.status_code == 200:
                    data = resp.json()
                    claims = data.get("claims", [])
                    if claims:
                        return {
                            "found": True,
                            "claims": len(claims),
                            "first_rating": claims[0].get("claimReview", [{}])[0].get("textualRating", "Unknown"),
                        }
            return {"found": False, "claims": 0}
        except Exception as e:
            logger.warning(f"Fact-check API error: {e}")
            return {"found": False, "claims": 0, "error": str(e)}