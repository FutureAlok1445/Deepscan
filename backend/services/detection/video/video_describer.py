import asyncio
import base64
import cv2
from loguru import logger
from backend.config import settings


class VideoDescriber:
    """
    Returns a structured forensic description of the video content.
    Uses LM Studio (local Qwen VL) via the OpenAI-compatible API for actual frame analysis.
    Falls back to Groq text-only description if LM Studio is unavailable.
    """

    def __init__(self):
        self.client = None
        self.model = None
        self._lm_studio_ok = False
        try:
            from openai import OpenAI
            self.client = OpenAI(
                base_url=settings.LMSTUDIO_BASE_URL,
                api_key="lm-studio"   # LM Studio doesn't need a real key
            )
            self.model = settings.LMSTUDIO_MODEL
            # Quick connectivity test — list models to confirm LM Studio is alive
            try:
                model_list = self.client.models.list()
                available = [m.id for m in model_list.data]
                logger.info(f"[VideoDescriber] LM Studio connected. Available models: {available}")
                if available:
                    # Use the first available model if configured one isn't found
                    if self.model not in available:
                        logger.warning(
                            f"[VideoDescriber] Configured model '{self.model}' not in LM Studio. "
                            f"Using '{available[0]}' instead."
                        )
                        self.model = available[0]
                    self._lm_studio_ok = True
                else:
                    logger.warning("[VideoDescriber] LM Studio is running but no models are loaded. Please load a model in LM Studio.")
            except Exception as conn_err:
                logger.warning(f"[VideoDescriber] LM Studio not reachable at {settings.LMSTUDIO_BASE_URL}: {conn_err}")
        except Exception as e:
            logger.warning(f"[VideoDescriber] Failed to initialize OpenAI client: {e}")

    async def describe(self, frames: list, filename: str = "") -> dict:
        """
        Describe the video content by analyzing visual frames via LM Studio (Qwen VL).
        """
        if not self.client or not self._lm_studio_ok or not frames:
            reason = "no frames" if not frames else ("LM Studio not running" if not self.client else "LM Studio model not loaded")
            logger.warning(f"[VideoDescriber] Skipping Qwen analysis: {reason}. Falling back to Groq.")
            return await self._fallback_describe(filename)

        try:
            # Sample up to 8 frames evenly
            step = max(1, len(frames) // 8)
            sampled_frames = frames[::step][:8]
            logger.info(f"[Qwen VL] Encoding {len(sampled_frames)} frames and sending to {self.model} at {settings.LMSTUDIO_BASE_URL}...")

            # Encode frames as base64 JPEG
            image_contents = []
            for f in sampled_frames:
                _, buffer = cv2.imencode('.jpg', f, [int(cv2.IMWRITE_JPEG_QUALITY), 75])
                b64 = base64.b64encode(buffer).decode('utf-8')
                image_contents.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                })

            prompt_text = """\
You are a senior forensic video analyst working for a deepfake and AI-manipulation detection laboratory. \
You have been handed a set of frame samples extracted at equal intervals from a video under investigation. \
Your task is to perform a meticulous multi-layer visual forensic analysis and produce a structured expert report.

════ FORENSIC INSPECTION CHECKLIST ════

[F1] SCENE INTELLIGENCE
- What is the physical setting? (indoors / outdoors, location type, time of day, lighting source)
- Are there multiple camera angles or cuts visible across these frames?

[F2] SUBJECT IDENTIFICATION
- How many distinct persons are visible? Describe each: approximate age, gender, ethnicity, attire, expressions.
- Are the subjects public figures, politicians, celebrities, or ordinary individuals?
- Note any text overlays, logos, branding, or watermarks visible in the frame.

[F3] ACTIVITY & NARRATIVE
- What is the subject doing? (speaking, walking, gesturing, sitting, etc.)
- What is the apparent narrative being conveyed? Is it a speech, interview, news clip, or staged scene?

[F4] VISUAL AUTHENTICITY INDICATORS — look for these specific deepfake signals:
- FACE BOUNDARY: Is there visible blending seam, color discontinuity, or soft-edge artifact around the face region?
- TEXTURE UNIFORMITY: Does facial skin appear unnaturally smooth, waxy, over-sharpened, or blurred compared to surrounding areas?
- EYE REGION: Are eyes over-bright, asymmetric, missing specular highlights, or showing abnormal iris rendering?
- LIP & TEETH: Are lip movements mechanical, do teeth appear unnaturally white/uniform, or does the mouth boundary flicker?
- TEMPORAL GLITCHING: Do any facial features seem to "pop", warp, or jitter between frames? Note frame index clues.
- HAIR/EARS: Is hair rendering unnaturally clean, poorly integrated, or does the ear region show artifacts?
- BACKGROUND CONSISTENCY: Does the background remain pixel-perfect stable while the subject moves? (GAN hallmark)
- LIGHTING PHYSICS: Does the light direction on the subject's face match the ambient lighting of the scene?
- SHADOW COHERENCE: Are cast shadows present, natural, and directionally consistent?
- COMPRESSION ARTIFACTS: Are there JPEG block artifacts, ringing, or unusual sharpness inconsistencies between face and background?

[F5] KEY MOMENTS (TEMPORAL LOG)
List 2-4 specific visual events observed across the frame sequence. Each entry should reference what changes or is notable.

[F6] CONTEXT & INTENT
- What is the apparent purpose of this video? (news, entertainment, political speech, scam bait, propaganda)
- Is the narrative plausible given the visual context, or does it appear staged or misleading?
- Are there any urgency-creating elements (countdown timers, QR codes, crisis language, investment claims)?

[F7] FORENSIC VERDICT — your expert opinion based purely on visual evidence:
- Rate likelihood of synthetic/deepfake manipulation on a scale: CLEAN / SUSPICIOUS / LIKELY_AI / DEFINITE_AI
- Summarize the top 2 most convincing visual artifacts you observed (or confirm their absence).

════ STRICT OUTPUT FORMAT (Follow Exactly) ════
SETTING: [single line]
PEOPLE: [single line describing all subjects]
ACTIVITY: [single line]
ARTIFACTS:
- [artifact 1, specific location and nature]
- [artifact 2]
- [artifact 3 or NONE DETECTED]
MOMENTS:
- [Frame event 1]
- [Frame event 2]
- [Frame event 3]
CONTEXT: [2-3 sentences on narrative intent and risk level]
VERDICT: [CLEAN | SUSPICIOUS | LIKELY_AI | DEFINITE_AI] — [one-sentence justification]
"""

            messages = [{
                "role": "user",
                "content": [{"type": "text", "text": prompt_text}] + image_contents
            }]

            # Call LM Studio in a thread (blocking I/O)
            logger.info(f"[Qwen VL] Awaiting response from LM Studio (model={self.model})...")
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=messages,
                max_tokens=900,
                temperature=0.15,
            )

            raw = response.choices[0].message.content.strip()
            logger.info(f"[Qwen VL] ✓ Got forensic response ({len(raw)} chars)")
            return self._parse_response(raw)

        except Exception as e:
            logger.error(f"[Qwen VL] ✗ LM Studio call FAILED: {e}. Falling back to Groq.")
            return await self._fallback_describe(filename)

    async def _fallback_describe(self, filename: str) -> dict:
        """Groq-based text-only fallback when LM Studio is not running."""
        try:
            from groq import Groq
            if not settings.GROQ_API_KEY:
                logger.warning("[VideoDescriber] No GROQ_API_KEY set — returning empty description.")
                return self._no_api_response()

            logger.info(f"[VideoDescriber] Using Groq fallback for '{filename}'")
            client = Groq(api_key=settings.GROQ_API_KEY)
            prompt = (
                f"Analyze video context for file: '{filename}'. "
                "API LIMITATION: No visual access. Infer a plausible description based on filename.\n"
                "Format: SETTING: .. PEOPLE: .. ACTIVITY: .. MOMENTS: .. CONTEXT: .."
            )

            response = await asyncio.to_thread(
                client.chat.completions.create,
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}]
            )
            return self._parse_response(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"[VideoDescriber] Groq fallback also failed: {e}")
            return self._no_api_response()

    def _parse_response(self, raw: str) -> dict:
        """Parse the structured forensic LLM response into a clean dict."""
        import re

        def first_match(pattern, text, default="Unknown"):
            m = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            return m.group(1).strip() if m else default

        def bullet_list(section_label, next_labels, text):
            """Extract a dash-prefixed bullet list from a section."""
            next_pattern = "|".join(re.escape(l) for l in next_labels)
            block_m = re.search(
                rf'{re.escape(section_label)}:\s*\n(.*?)(?=\n(?:{next_pattern}):|$)',
                text, re.IGNORECASE | re.DOTALL
            )
            if not block_m:
                return []
            lines = block_m.group(1).splitlines()
            return [l.lstrip("-•* ").strip() for l in lines if l.strip() and len(l.strip()) > 3]

        setting  = first_match(r'SETTING:\s*(.*?)(?=\nPEOPLE:|$)', raw, "Unknown")
        people   = first_match(r'PEOPLE:\s*(.*?)(?=\nACTIVITY:|$)', raw, "Unknown")
        activity = first_match(r'ACTIVITY:\s*(.*?)(?=\nARTIFACTS:|$)', raw, "Inconclusive")
        context  = first_match(r'CONTEXT:\s*(.*?)(?=\nVERDICT:|$)', raw, "General observation")
        verdict_line = first_match(r'VERDICT:\s*(.*?)$', raw, "")

        artifacts = bullet_list("ARTIFACTS", ["MOMENTS", "CONTEXT", "VERDICT"], raw)
        moments   = bullet_list("MOMENTS",   ["CONTEXT", "VERDICT"], raw)

        # Extract verdict level: CLEAN / SUSPICIOUS / LIKELY_AI / DEFINITE_AI
        verdict_level = "UNKNOWN"
        v_match = re.search(r'\b(CLEAN|SUSPICIOUS|LIKELY_AI|DEFINITE_AI)\b', verdict_line, re.IGNORECASE)
        if v_match:
            verdict_level = v_match.group(1).upper()

        return {
            "description": raw,
            "setting":     setting,
            "people":      people,
            "activity":    activity,
            "artifacts":   [a for a in artifacts if "NONE" not in a.upper()],
            "moments":     moments,
            "context":     context,
            "verdict":     verdict_level,
            "verdict_detail": verdict_line,
        }

    def _no_api_response(self) -> dict:
        return {
            "description": "Video description unavailable. LM Studio not running and no Groq API key set.",
            "setting": "N/A", "people": "N/A", "activity": "N/A",
            "artifacts": [], "moments": [], "context": "N/A",
            "verdict": "UNKNOWN", "verdict_detail": ""
        }
