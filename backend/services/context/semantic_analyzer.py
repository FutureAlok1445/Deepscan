import asyncio
import base64
from loguru import logger

HAS_CV2 = False
try:
    import cv2
    HAS_CV2 = True
except ImportError:
    cv2 = None
    logger.warning("cv2 not installed — SemanticAnalyzer image encoding will use PIL fallback")

from backend.config import settings


class SemanticAnalyzer:
    """
    Uses LM Studio (local Qwen3 VL) for true scene analysis and claim extraction.
    Claims are used for factual verification against global news.
    Falls back gracefully if LM Studio is not running.
    """

    def __init__(self):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=settings.LMSTUDIO_BASE_URL,
                api_key="lm-studio"
            )
            self.model = settings.LMSTUDIO_MODEL
            logger.info(f"SemanticAnalyzer initialized (LM Studio / {self.model})")
        except Exception as e:
            logger.warning(f"SemanticAnalyzer: LM Studio client failed: {e}. Fallback mode.")
            self.client = None
            self.model = None

    async def describe_and_verify(self, frames: list) -> dict:
        """
        1. Analyzes visual frames for deep semantic meaning.
        2. Extracts specific factual claims (e.g., 'Joe Biden is in Kyiv').
        """
        if not self.client or not frames:
            return {"description": "Semantic analysis unavailable (LM Studio not running).", "claims": []}

        try:
            # Sample 5 frames for deep analysis
            step = max(1, len(frames) // 5)
            sampled = frames[::step][:5]

            image_contents = []
            for f in sampled:
                _, buffer = cv2.imencode('.jpg', f, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                b64 = base64.b64encode(buffer).decode('utf-8')
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

            prompt_text = """\
You are a senior intelligence analyst specializing in open-source intelligence (OSINT) and media disinformation. \
You have been assigned a set of frame samples from a video under investigation for possible deepfake manipulation \
or coordinated disinformation. Your task is to perform a structured factual analysis.

════ INTELLIGENCE ANALYSIS CHECKLIST ════

[I1] SCENE & SETTING ASSESSMENT
- Describe the physical environment: location type, apparent country/region (based on visual cues like signage, architecture, flags), and time of day.
- Is the production quality consistent with professional media, citizen journalism, or synthetic generation?

[I2] SUBJECT IDENTIFICATION & CREDIBILITY
- Identify any recognizable individuals. If you recognize a public figure (politician, executive, TV presenter, etc.), name them and note their jurisdiction/role.
- If the person is NOT identifiable, describe them objectively.
- Assess body language: does the person appear natural, coached, stilted, or digitally substituted?

[I3] FACTUAL CLAIM EXTRACTION (Critical — be specific)
Extract every verifiable claim visible or implied in these frames. For each claim:
- State the claim as a standalone assertion (e.g., "Prime Minister X announces free investment scheme")
- Classify: POLITICAL / FINANCIAL / HEALTH / LEGAL / GEOGRAPHIC / SOCIAL
- Rate claim plausibility: PLAUSIBLE / QUESTIONABLE / SUSPICIOUS / IMPLAUSIBLE

[I4] MANIPULATION INDICATORS — look for these specific disinformation patterns:
- VISUAL FABRICATION: Face replacement, background substitution, synthetic generation artifacts
- CONTEXT MANIPULATION: Authentic footage recontextualized to convey a false event
- TEMPORAL DECEPTION: Old footage presented as current events (check visible date stamps, seasonal cues)
- GEOGRAPHIC MISREPRESENTATION: Footage attributed to wrong location (check flags, license plates, signage language)
- AUDIO-VISUAL MISMATCH: Lip-sync anomalies, dubbed speech, subtitles that contradict facial expressions
- URGENCY ENGINEERING: Countdown timers, QR codes, phone numbers, crisis language, investment hooks
- AUTHORITY SPOOFING: Fake logos, impersonated news tickers, forged credentials or government seals

[I5] NARRATIVE INTENT ANALYSIS
- What is the most likely PURPOSE of this video? (legitimate news / political education / scam / propaganda / harassment / satire)
- Who is the TARGET AUDIENCE? (general public / specific demographic / investors / voters)
- What BEHAVIOR is this video likely trying to induce? (buy something / vote / panic / share / believe falsehood)

[I6] RISK ASSESSMENT
Rate the overall disinformation risk: LOW / MEDIUM / HIGH / CRITICAL
- LOW: Authentic content, no manipulation detected
- MEDIUM: Possible misrepresentation but claims are verifiable  
- HIGH: Strong indicators of synthetic media or deliberate deception
- CRITICAL: Clear deepfake or coordinated disinformation with harm potential

════ STRICT OUTPUT FORMAT ════
DESCRIPTION: [1-2 sentences: objective scene summary]
SUBJECTS: [identified or described persons]
CLAIMS:
- [Claim 1]: [CATEGORY] — [PLAUSIBILITY]
- [Claim 2]: [CATEGORY] — [PLAUSIBILITY]
- [Claim 3 or NONE]: [CATEGORY] — [PLAUSIBILITY]
MANIPULATION_INDICATORS:
- [Indicator 1 observed or NONE DETECTED]
- [Indicator 2]
NARRATIVE_INTENT: [purpose | target audience | induced behavior]
RISK: [LOW | MEDIUM | HIGH | CRITICAL] — [one sentence justification]
"""

            messages = [{
                "role": "user",
                "content": [{"type": "text", "text": prompt_text}] + image_contents
            }]

            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=800,
                temperature=0.1,
            )

            raw_text = response.choices[0].message.content.strip()
            logger.info(f"SemanticAnalyzer (LM Studio/{self.model}): got {len(raw_text)} chars")

            import re

            def extract_section(label, next_labels, text):
                """Extract text between label and the next section label."""
                pattern = rf'{re.escape(label)}:\s*(.*?)(?=\n(?:{"|".join(re.escape(l) for l in next_labels)}):|$)'
                m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                return m.group(1).strip() if m else ""

            def extract_bullets(label, text):
                """Extract dash/bullet list under a section label."""
                m = re.search(rf'{re.escape(label)}:\s*\n((?:\s*[-•*]\s*.+\n?)+)', text, re.IGNORECASE)
                if not m:
                    return []
                return [line.lstrip("-•* ").strip() for line in m.group(1).splitlines() if line.strip()]

            all_labels = ["DESCRIPTION", "SUBJECTS", "CLAIMS", "MANIPULATION_INDICATORS", "NARRATIVE_INTENT", "RISK"]

            description        = extract_section("DESCRIPTION", all_labels[1:], raw_text)
            subjects           = extract_section("SUBJECTS", all_labels[2:], raw_text)
            claims_raw         = extract_bullets("CLAIMS", raw_text)
            manipulation_raw   = extract_bullets("MANIPULATION_INDICATORS", raw_text)
            narrative_intent   = extract_section("NARRATIVE_INTENT", all_labels[5:], raw_text)
            risk_line          = extract_section("RISK", [], raw_text)

            # Parse claims into structured dicts
            claims = []
            for c in claims_raw:
                if c.upper() in ["NONE", "NONE DETECTED", ""]:
                    continue
                parts = c.split(":")
                claim_text = parts[0].strip()
                meta = parts[1].strip() if len(parts) > 1 else ""
                cat_m = re.search(r'(POLITICAL|FINANCIAL|HEALTH|LEGAL|GEOGRAPHIC|SOCIAL)', meta, re.IGNORECASE)
                plaus_m = re.search(r'(PLAUSIBLE|QUESTIONABLE|SUSPICIOUS|IMPLAUSIBLE)', meta, re.IGNORECASE)
                claims.append({
                    "text": claim_text,
                    "category": cat_m.group(1).upper() if cat_m else "UNKNOWN",
                    "plausibility": plaus_m.group(1).upper() if plaus_m else "UNKNOWN"
                })

            risk_level = "UNKNOWN"
            risk_match = re.search(r'\b(LOW|MEDIUM|HIGH|CRITICAL)\b', risk_line, re.IGNORECASE)
            if risk_match:
                risk_level = risk_match.group(1).upper()

            return {
                "description": description,
                "subjects": subjects,
                "claims": claims,
                "manipulation_indicators": [m for m in manipulation_raw if "NONE" not in m.upper()],
                "narrative_intent": narrative_intent,
                "risk_level": risk_level,
                "risk_justification": risk_line,
                "raw": raw_text
            }

        except Exception as e:
            logger.error(f"SemanticAnalyzer (LM Studio) failed: {e}")
            return {"description": "Factual verification system encountered an error.", "claims": [], "risk_level": "UNKNOWN"}
