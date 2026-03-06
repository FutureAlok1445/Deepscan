"""
VideoNLMReport - Groq-powered Forensic Analysis Report Generator
Uses Groq's free-tier API (llama-3.3-70b-versatile) to generate
specific, reasoning-based forensic reports from the video scan metrics.
Falls back to the local deterministic engine if Groq API key is missing.
"""
from loguru import logger
from backend.config import settings


class VideoNLMReport:
    """
    Primary engine: Groq API (llama-3.3-70b-versatile)
    Fallback: Local deterministic expert system
    """
    def __init__(self):
        self.model = "llama-3.3-70b-versatile"
        logger.info("VideoNLMReport initialized (Groq backend).")

    async def generate_report(self, mas_score: float, spatial_score: float, temporal_penalty: float,
                              noise_score: float, artifact_penalty: float, ltca_data: dict, rppg_data: dict = None) -> str:
        groq_key = settings.GROQ_API_KEY
        if groq_key:
            try:
                report = await self._generate_with_groq(
                    groq_key, mas_score, spatial_score, temporal_penalty, noise_score, artifact_penalty, ltca_data, rppg_data
                )
                if report:
                    return report
            except Exception as e:
                logger.warning(f"Groq API failed, falling back to local engine: {e}")

        logger.info("Using local deterministic NLM engine.")
        return self._generate_local(mas_score, spatial_score, temporal_penalty, noise_score, artifact_penalty, ltca_data, rppg_data)

    async def _generate_with_groq(self, api_key: str, mas_score: float, spatial_score: float,
                                   temporal_penalty: float, noise_score: float, artifact_penalty: float, ltca_data: dict, rppg_data: dict = None) -> str:
        import asyncio
        from groq import Groq

        ltca_suspect = ltca_data.get('is_fake', False)
        curvature    = ltca_data.get('curvature_score', 0.0)
        velocity_var = ltca_data.get('velocity_variance', 0.0)
        ltca_reason  = ltca_data.get('reason', 'No LTCA anomalies detected.')

        verdict = "Authentic" if mas_score < 40 else "AI-Generated Deepfake" if mas_score >= 60 else "Suspicious"

        # Pre-interpret each metric into plain English before sending to Groq.
        # This forces Groq to reason from meaning, not just repeat raw numbers.
        if spatial_score < 35:
            spatial_interp = (
                f"clean ({spatial_score:.0f}/100) — the FFT frequency spectrum is rich in high-frequency "
                f"texture detail, block variance is high, and edge sharpness is consistent with real camera "
                f"sensor capture. No diffusion smoothing or GAN upsampling artifacts found."
            )
        elif spatial_score < 65:
            spatial_interp = (
                f"moderately suspicious ({spatial_score:.0f}/100) — the frequency domain shows elevated "
                f"low-frequency energy relative to high-frequency content. Local pixel blocks are more "
                f"uniform than expected for real camera footage, suggesting partial AI synthesis or "
                f"significant post-processing."
            )
        else:
            spatial_interp = (
                f"strongly anomalous ({spatial_score:.0f}/100) — the FFT spectrum clearly shows diffusion "
                f"model or GAN artifacts: suppressed high-frequency content, unnaturally uniform image "
                f"blocks, missing PRNU (Photo Response Non-Uniformity) sensor fingerprint, and over-smoothed "
                f"edges typical of AI-generated imagery."
            )

        if temporal_penalty < 30:
            temporal_interp = (
                f"natural ({temporal_penalty:.0f}/100) — optical flow vectors between frames follow "
                f"physically plausible trajectories with organic variation and acceleration curves."
            )
        elif temporal_penalty < 60:
            temporal_interp = (
                f"mildly inconsistent ({temporal_penalty:.0f}/100) — some inter-frame motion vectors show "
                f"slightly unnatural transitions that could indicate AI frame interpolation, though also "
                f"consistent with heavy video compression."
            )
        else:
            temporal_interp = (
                f"severely anomalous ({temporal_penalty:.0f}/100) — optical flow analysis reveals "
                f"discontinuous motion vectors and non-physical frame morphing patterns, strongly consistent "
                f"with AI video synthesis rather than real camera motion."
            )

        if noise_score < 8:
            noise_interp = (
                f"suspiciously smooth ({noise_score:.0f}/100) — the noise floor is unnaturally low and "
                f"lacks the organic PRNU fingerprint of a real camera sensor, which is a key signature "
                f"of diffusion model output."
            )
        else:
            noise_interp = (
                f"within normal range ({noise_score:.0f}/100) — noise distribution is consistent with "
                f"standard camera sensor characteristics and video compression."
            )

        if ltca_suspect:
            physics_interp = (
                f"VIOLATION DETECTED — {ltca_reason}. Curvature index {curvature:.3f} (authentic video "
                f"threshold >0.25) shows the video's latent trajectory collapses, meaning momentum vectors "
                f"violate Newtonian physics. Velocity variance {velocity_var:.3f} confirms impossible "
                f"speed discontinuities between frames that no real camera motion produces."
            )
        else:
            physics_interp = (
                f"no violations — latent trajectory curvature {curvature:.3f} and velocity variance "
                f"{velocity_var:.3f} are both within normal ranges for real-world camera motion."
            )

        if not rppg_data:
            rppg_interp = "No biological heartbeat data available or extracted."
        elif rppg_data.get('confidence', 0) < 0.2 or rppg_data.get('heart_rate', 0) == 0:
            rppg_interp = (
                f"critical biological failure — Remote Photoplethysmography (rPPG) could not "
                f"detect a valid human heartbeat or micro-circulation in the facial pixels. "
                f"A real human face exhibits rhythmic color changes with every heartbeat. "
                f"The lack of this signal strongly suggests this face was mathematically generated "
                f"rather than physically recorded."
            )
        else:
            rppg_interp = (
                f"normal biological signature — a valid human heartbeat of {rppg_data.get('heart_rate', 0)} "
                f"BPM was successfully extracted from facial micro-color fluctuations, confirming the "
                f"presence of actual blood flow under the skin (a very strong indicator of a real video)."
            )

        if artifact_penalty < 30:
            artifact_interp = (
                f"clean ({artifact_penalty:.0f}/100) — no low-level deepfake artifacts detected. Edge contrast "
                f"varies naturally across the frame, chroma values are consistent, and no structural grid/block "
                f"anomalies typically associated with GAN upsampling or face-swapping boundaries are present."
            )
        else:
            artifact_interp = (
                f"critical artifacts detected ({artifact_penalty:.0f}/100) — local pixel analysis reveals distinct "
                f"deepfake signatures, such as unnatural blending boundaries (often from masking a synthetic face "
                f"onto a real target), over-smoothed chroma channels, or subtle grid-like macroblock structures "
                f"introduced by generative AI upsamplers."
            )

        prompt = (
            f"You are an expert digital forensics analyst. A user just uploaded a video for you to analyze. "
            f"Your job is to explain to them EXACTLY why this video is {verdict} based on the forensic data below.\n\n"
            f"THE DATA:\n"
            f"- Overall Authenticities Score: {mas_score:.1f}/100 (where >60 means AI deepfake, <40 means real)\n"
            f"- Pixel/Spatial Analysis: {spatial_interp}\n"
            f"- Generative Artifact Analysis: {artifact_interp}\n"
            f"- Motion Analysis: {temporal_interp}\n"
            f"- Noise Fingerprint: {noise_interp}\n"
            f"- Physics/Momentum: {physics_interp}\n"
            f"- Biological/Heartbeat Analysis (rPPG): {rppg_interp}\n\n"
            f"INSTRUCTIONS:\n"
            f"Write a natural, conversational 3-paragraph explanation. Talk directly to the user.\n"
            f"Do NOT write like a robot. NEVER use robotic templates like 'The Deepscan pipeline computed a Media Authenticity Score of...' or 'Analysis indicates that...'.\n"
            f"Instead, speak like a real human expert who just looked at the data. For example:\n"
            f"'Looking at this video, it scores a {mas_score:.1f}/100, which puts it firmly in the {verdict} category. The biggest giveaway here is the biological data...'\n\n"
            f"Paragraph 1: State clearly if it's real or AI, referencing the overall score.\n"
            f"Paragraph 2: Explain the biological heartbeat findings first (if any), then detail the pixel and noise anomalies.\n"
            f"Paragraph 3: Explain the physics momentum or motion anomalies and give your final recommendation.\n"
        )

        loop = asyncio.get_event_loop()

        def _call_groq():
            client = Groq(api_key=api_key)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.65,
                max_tokens=620,
            )
            return response.choices[0].message.content.strip()

        report = await loop.run_in_executor(None, _call_groq)
        logger.success(f"Groq NLM report generated ({len(report)} chars).")
        return report

    def _generate_local(self, mas_score: float, spatial_score: float, temporal_penalty: float,
                        noise_score: float, artifact_penalty: float, ltca_data: dict, rppg_data: dict = None) -> str:
        """Local deterministic fallback."""
        ltca_suspect = ltca_data.get('is_fake', False)
        curvature = ltca_data.get('curvature_score', 0.0)
        velocity_var = ltca_data.get('velocity_variance', 0.0)
        ltca_reason = ltca_data.get('reason', 'No anomalies detected.')

        if mas_score < 30:
            p1 = (f"This video scored {mas_score:.1f}/100 on the authenticity scale — a strong indicator of "
                  f"genuine camera footage. At this score, all four forensic vectors (spatial, temporal, "
                  f"physics, noise) found no significant evidence of AI generation.")
        elif mas_score < 55:
            p1 = (f"This video scored {mas_score:.1f}/100 — in the uncertain zone where signals are mixed. "
                  f"Some detectors found mild anomalies while others found nothing suspicious. This score "
                  f"can result from heavy video compression, lossy re-encoding, or subtle editing.")
        else:
            p1 = (f"This video scored {mas_score:.1f}/100 — well into the AI-generated range. Multiple "
                  f"independent forensic vectors converged on the same conclusion: this video shows "
                  f"consistent characteristics of AI synthesis rather than real camera capture.")

        sp = "found no pixel-level anomalies" if spatial_score < 35 else f"detected spatial anomalies ({spatial_score:.1f}/100) — elevated low-frequency FFT energy and uniform block regions typical of AI upsampling" if spatial_score < 65 else f"strongly flagged ({spatial_score:.1f}/100) — clear diffusion smoothing, no real sensor PRNU, over-smooth edges"
        tp = "confirmed natural optical flow" if temporal_penalty < 30 else f"detected mild motion inconsistencies ({temporal_penalty:.1f}/100)" if temporal_penalty < 60 else f"detected severe motion anomalies ({temporal_penalty:.1f}/100) — discontinuous flow vectors inconsistent with camera physics"
        p2 = f"The spatial engine {sp}. The temporal engine {tp}."

        if ltca_suspect:
            p3 = (f"Physics engine: {ltca_reason} Curvature {curvature:.3f}, velocity variance "
                  f"{velocity_var:.3f} — RECOMMENDATION: FLAG AS SYNTHETIC MEDIA.")
        else:
            p3 = (f"Physics engine found no violations (curvature {curvature:.3f}, velocity variance "
                  f"{velocity_var:.3f}). Noise score: {noise_score:.1f}/100. "
                  f"RECOMMENDATION: {'CLEAR.' if mas_score < 30 else 'FURTHER REVIEW RECOMMENDED.' if mas_score < 55 else 'FLAG AS SYNTHETIC MEDIA.'}")

        return f"{p1}\n\n{p2}\n\n{p3}"
