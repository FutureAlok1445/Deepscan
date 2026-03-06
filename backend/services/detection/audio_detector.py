"""
audio_detector.py — 7-Signature Audio Deepfake Detection System

Complete science-based audio analysis pipeline:
  Sig 1: F0 Stability Analysis (25%)     — pYIN fundamental frequency
  Sig 2: MFCC Delta Variance (20%)        — Articulatory dynamics
  Sig 3: Spectrogram Texture (20%)        — HPSS + vocoder pattern detection
  Sig 4: Breathing / Silence Analysis (15%) — Micro-pause & breathing band
  Sig 5: Phase Discontinuity (10%)        — STFT phase jump detection
  Sig 6: HuggingFace wav2vec2 (5%)        — Pre-trained audio classification
  Sig 7: Groq Whisper + Llama (5%)        — Transcript-level AI analysis

Weighted AAS = 0.25×F0 + 0.20×MFCC + 0.20×Spectral + 0.15×Breathing
             + 0.10×Phase + 0.05×HF + 0.05×Groq
"""

import os
import asyncio
import time
import traceback
import numpy as np
from loguru import logger

from backend.config import settings
from backend.utils.audio_utils import (
    load_audio,
    extract_f0,
    extract_mfcc_features,
    extract_spectral_features,
    analyze_silence_breathing,
    compute_phase_features,
    generate_spectrogram_image,
    get_audio_duration,
)
from backend.services.forensics.spectrogram_analyzer import (
    analyze_spectrogram_for_synthesis,
    check_for_gan_vocoder_patterns,
)


# =====================================================================
# WEIGHTS — Phase 8: 9-Signature Pipeline
# =====================================================================
WEIGHTS = {
    "f0": 0.20,         # Fundamental frequency stability
    "vtl": 0.15,        # Vocal Tract Length consistency (NEW)
    "spectral": 0.15,   # Spectrogram texture & vocoder patterns
    "mirroring": 0.10,  # Spectral mirroring artifacts (NEW)
    "mfcc": 0.15,       # Articulatory dynamics
    "breathing": 0.10,  # Micro-silence & breathing
    "phase": 0.05,      # STFT phase discontinuities
    "hf": 0.05,         # External ViT/Wav2Vec models
    "groq": 0.05,       # Semantic/Transcript analysis
}


# =====================================================================
# Scoring Helpers
# =====================================================================
def _clamp(score: float) -> float:
    """Clamp score to [0, 100]."""
    return round(min(100.0, max(0.0, score)), 1)


def _compute_weighted_aas(scores: dict) -> float:
    """Compute the weighted Audio Authenticity Score."""
    total = 0.0
    weight_sum = 0.0
    for key, weight in WEIGHTS.items():
        if key in scores and scores[key] is not None:
            total += weight * scores[key]
            weight_sum += weight

    if weight_sum > 0:
        return _clamp(total / weight_sum * sum(WEIGHTS.values()))
    return 50.0


def _generate_findings(scores: dict, details: dict) -> list:
    """
    Generate structured findings with reasoning.
    Returns a list of dicts: {"engine": str, "score": float, "detail": str, "reasoning": str}
    """
    findings = []

    # Mapping of score keys to display names and logic
    engine_map = {
        "f0": "F0-Stability-Analysis",
        "vtl": "Vocal-Tract-Consistency",
        "spectral": "Spectrogram-Texture",
        "mirroring": "Spectral-Mirroring-Check",
        "mfcc": "MFCC-Articulatory-Dynamics",
        "breathing": "Breathing-Silence-Pattern",
        "phase": "Phase-Discontinuity-Detector",
        "hf": "HuggingFace-Wav2Vec2",
        "groq": "Groq-Transcript-Linguistic",
    }

    for key, engine_name in engine_map.items():
        score = scores.get(key, 50.0)
        detail_data = details.get(key, {})
        
        # Pull reasoning from the sub-module result if available
        reasoning = detail_data.get("reasoning", "")
        detail_str = detail_data.get("detail", "")
        
        if not reasoning:
            # Fallback reasoning for engines that don't provide it yet
            if key == "hf":
                reasoning = "External inference via HuggingFace transformers (wav2vec2), matching acoustic signatures against known synthetic manifolds."
            elif key == "groq":
                reasoning = detail_data.get("analysis_summary", "Linguistic analysis of transcript patterns (filler words, disfluencies, and robotic phrasing).")
            else:
                reasoning = f"Analysis of {engine_name} parameters to identify statistical deviations from natural human speech."

        findings.append({
            "engine": engine_name,
            "score": round(score, 1),
            "detail": detail_str if detail_str else f"Score: {score:.1f}",
            "reasoning": reasoning
        })

    return findings


# =====================================================================
# Groq Integration (Whisper + Llama)
# =====================================================================
async def _transcribe_with_groq(file_path: str) -> str:
    """Transcribe audio using Groq's Whisper-large-v3 API.

    Returns transcript text, or empty string on failure.
    """
    api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        logger.debug("Groq API key not configured — skipping transcription")
        return ""

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)

        # Read audio file
        with open(file_path, "rb") as f:
            audio_data = f.read()

        # Determine file name for the API
        filename = os.path.basename(file_path)
        if not filename.lower().endswith((".wav", ".mp3", ".m4a", ".flac", ".ogg", ".webm")):
            filename = filename + ".wav"

        transcription = await client.audio.transcriptions.create(
            model="whisper-large-v3",
            file=(filename, audio_data),
            response_format="text",
            language="en",
        )

        text = str(transcription).strip()
        logger.debug(f"Groq Whisper transcript: {text[:100]}...")
        return text

    except Exception as e:
        logger.warning(f"Groq Whisper transcription failed: {e}")
        return ""


async def _analyze_transcript_with_groq(transcript: str) -> dict:
    """Analyze transcript with Groq Llama to detect AI speech patterns.

    Asks Llama to evaluate the transcript for:
    - Unnatural sentence structures
    - Repetitive phrasing
    - Missing filler words / hedging
    - Overly formal or robotic language
    - Lack of self-corrections or disfluencies

    Returns:
        dict with keys: score (0-100), analysis_summary (str)
    """
    api_key = settings.GROQ_API_KEY or os.environ.get("GROQ_API_KEY", "")
    if not api_key or not transcript or len(transcript.strip()) < 10:
        return {"score": 50.0, "analysis_summary": "Insufficient data"}

    try:
        from groq import AsyncGroq
        client = AsyncGroq(api_key=api_key)

        prompt = f"""You are an expert linguist analyzing a speech transcript for signs of AI-generated audio. 
Real human speech typically contains:
- Filler words (um, uh, like, you know)
- Self-corrections and restarts
- Varied sentence lengths
- Informal contractions
- Natural hesitation and disfluencies

AI-generated speech often has:
- Perfectly formed sentences
- No filler words or disfluencies
- Overly consistent rhythm and pacing
- Repetitive phrasing patterns
- Unnaturally formal or polished language

Transcript to analyze:
\"\"\"{transcript[:2000]}\"\"\"

Respond with ONLY a JSON object (no markdown, no explanation):
{{"score": <0-100 where 100 means definitely AI-generated>, "reason": "<one sentence explanation>"}}"""

        response = await client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=150,
        )

        text = response.choices[0].message.content.strip()
        logger.debug(f"Groq Llama analysis: {text[:200]}")

        # Parse JSON response
        import json
        # Try to extract JSON from response
        if "{" in text and "}" in text:
            json_str = text[text.index("{"):text.rindex("}") + 1]
            parsed = json.loads(json_str)
            score = float(parsed.get("score", 50))
            reason = str(parsed.get("reason", ""))
            return {"score": _clamp(score), "analysis_summary": reason}

        return {"score": 50.0, "analysis_summary": "Could not parse Llama response"}

    except Exception as e:
        logger.warning(f"Groq Llama analysis failed: {e}")
        return {"score": 50.0, "analysis_summary": f"Analysis failed: {str(e)[:80]}"}


# =====================================================================
# HuggingFace Integration (wav2vec2)
# =====================================================================
async def _query_huggingface_audio(file_path: str) -> float:
    """Query HuggingFace Inference API with wav2vec2 for audio classification.

    Uses the facebook/wav2vec2-base-960h model or a deepfake-specific model.
    Returns score 0-100 where 100 = definitely AI.
    """
    api_key = (
        settings.HUGGINGFACE_API_KEY
        or settings.HF_API_TOKEN
        or os.environ.get("HUGGINGFACE_API_KEY", "")
        or os.environ.get("HF_API_TOKEN", "")
    )
    if not api_key:
        logger.debug("HuggingFace API key not configured — skipping HF inference")
        return 50.0

    import httpx

    # Try specialized deepfake audio detection model first, fall back to general
    models_to_try = [
        "motheecreator/Deepfake-audio-detection",
        "umm-maybe/AI-Voice-Detector",
    ]

    for model_id in models_to_try:
        try:
            url = f"https://api-inference.huggingface.co/models/{model_id}"
            headers = {"Authorization": f"Bearer {api_key}"}

            async with httpx.AsyncClient(timeout=30.0) as client:
                with open(file_path, "rb") as f:
                    data = f.read()
                response = await client.post(url, headers=headers, content=data)

            if response.status_code == 200:
                result = response.json()
                score = _parse_hf_result(result)
                if score is not None:
                    logger.debug(f"HuggingFace ({model_id}): score={score}")
                    return score
            elif response.status_code == 503:
                # Model loading — try next
                logger.debug(f"HuggingFace model {model_id} is loading, trying next")
                continue
            else:
                logger.debug(f"HuggingFace {model_id} returned {response.status_code}")
                continue

        except Exception as e:
            logger.debug(f"HuggingFace {model_id} failed: {e}")
            continue

    logger.debug("All HuggingFace models failed — returning neutral")
    return 50.0


def _parse_hf_result(result) -> float | None:
    """Parse HuggingFace audio classification result into a fake probability 0-100."""
    fake_labels = {"fake", "spoof", "ai", "synthetic", "label_1", "deepfake", "ai-generated"}
    real_labels = {"real", "bonafide", "human", "label_0", "authentic", "genuine"}

    if isinstance(result, list):
        for item in result:
            if isinstance(item, list):
                # Nested list (common for audio classification)
                for sub in item:
                    label = str(sub.get("label", "")).lower().strip()
                    conf = float(sub.get("score", 0))
                    if label in fake_labels:
                        return _clamp(conf * 100)
                    if label in real_labels:
                        return _clamp((1 - conf) * 100)
            elif isinstance(item, dict):
                label = str(item.get("label", "")).lower().strip()
                conf = float(item.get("score", 0))
                if label in fake_labels:
                    return _clamp(conf * 100)
                if label in real_labels:
                    return _clamp((1 - conf) * 100)

    elif isinstance(result, dict):
        label = str(result.get("label", "")).lower().strip()
        conf = float(result.get("score", 0))
        if label in fake_labels:
            return _clamp(conf * 100)
        if label in real_labels:
            return _clamp((1 - conf) * 100)

    return None


# =====================================================================
# Spectrum data builder (for frontend AudioSpectrum component)
# =====================================================================
def _build_spectrum_data(audio: np.ndarray, sr: int = 16000) -> list:
    """Build frequency spectrum data for the frontend AudioSpectrum chart.

    Returns list of {freq, amplitude, freq_hz} dicts, downsampled to ~64 bins.
    """
    from scipy.fft import rfft, rfftfreq

    n = len(audio)
    if n < 256:
        return []

    window = np.hanning(n)
    windowed = audio * window
    yf = rfft(windowed)
    xf = rfftfreq(n, 1.0 / sr)
    magnitude = np.abs(yf) / n
    magnitude = np.clip(magnitude, 1e-10, None)
    power_db = 20.0 * np.log10(magnitude)

    num_bins = 64
    if len(xf) > num_bins:
        indices = np.linspace(0, len(xf) - 1, num_bins, dtype=int)
    else:
        indices = np.arange(len(xf))

    spectrum = []
    for idx in indices:
        freq_hz = float(xf[idx])
        amp = float(power_db[idx])
        freq_label = f"{freq_hz / 1000:.1f}kHz" if freq_hz >= 1000 else f"{freq_hz:.0f}Hz"
        spectrum.append({
            "freq": freq_label,
            "amplitude": round(max(amp, 0), 1),
            "freq_hz": round(freq_hz, 1),
        })

    return spectrum


# =====================================================================
# MAIN DETECTION FUNCTION
# =====================================================================
async def detect_audio(file_path: str) -> dict:
    """Run the complete 7-signature audio deepfake detection pipeline.

    This is the main entry point called by the orchestrator.

    Args:
        file_path: Path to audio file (WAV, MP3, M4A, FLAC, OGG, or video with audio track)

    Returns:
        dict with keys:
        - aas_score: float 0-100 (weighted Audio Authenticity Score)
        - verdict: str ("LIKELY REAL", "UNCERTAIN", "LIKELY AI-GENERATED")
        - signature_scores: dict of individual signature scores
        - signature_details: dict of detailed analysis per signature
        - findings: list of human-readable finding strings
        - spectrum: list of {freq, amplitude, freq_hz} for frontend chart
        - spectrogram_png: bytes of mel spectrogram image (base64-encodable)
        - anomalies: list of detected anomaly dicts
        - splicing_detected: bool
        - clone_probability: float 0-100
        - duration_seconds: float
        - processing_time_ms: int
    """
    start_time = time.time()
    logger.info(f"AudioDetector: Starting 9-signature analysis on {os.path.basename(file_path)}")

    # ─── Step 1: Load Audio ───
    try:
        from backend.utils.audio_utils import (
            extract_formant_features,
            detect_spectral_mirroring
        )
        audio, sr = load_audio(file_path, sr=16000)
        duration = len(audio) / sr
        logger.info(f"AudioDetector: Loaded audio — {duration:.1f}s, {sr}Hz")
    except Exception as e:
        logger.error(f"AudioDetector: Failed to load audio: {e}")
        return _build_error_response(str(e), time.time() - start_time)

    if len(audio) < sr * 0.5:
        return _build_error_response("Audio too short (< 0.5s)", time.time() - start_time)

    # ─── Step 2: Run all 9 signatures ───
    loop = asyncio.get_running_loop()
    scores, details = {}, {}

    try:
        (f0_res, mfcc_res, spectral_base, breathing_res, phase_res,
         spec_synth, vocoder_res, vtl_res, mirroring_res, 
         spectrum_data, spectrogram_png) = await asyncio.gather(
            loop.run_in_executor(None, extract_f0, audio, sr),
            loop.run_in_executor(None, extract_mfcc_features, audio, sr),
            loop.run_in_executor(None, extract_spectral_features, audio, sr),
            loop.run_in_executor(None, analyze_silence_breathing, audio, sr),
            loop.run_in_executor(None, compute_phase_features, audio, sr),
            loop.run_in_executor(None, analyze_spectrogram_for_synthesis, audio, sr),
            loop.run_in_executor(None, check_for_gan_vocoder_patterns, audio, sr),
            loop.run_in_executor(None, extract_formant_features, audio, sr),
            loop.run_in_executor(None, detect_spectral_mirroring, audio, sr),
            loop.run_in_executor(None, _build_spectrum_data, audio, sr),
            loop.run_in_executor(None, generate_spectrogram_image, audio, sr),
        )
    except Exception as e:
        logger.error(f"Signal analysis failed: {e}")
        return _build_error_response(f"Signal Analysis Error: {e}", time.time() - start_time)

    # Populate 9-engine scores
    scores["f0"] = f0_res.get("score", 50.0)
    scores["mfcc"] = mfcc_res.get("score", 50.0)
    scores["breathing"] = breathing_res.get("score", 50.0)
    scores["phase"] = phase_res.get("score", 50.0)
    scores["vtl"] = vtl_res.get("score", 50.0)
    scores["mirroring"] = mirroring_res.get("score", 50.0)

    # Spectral score (consensus of 3 spectral sub-modules)
    scores["spectral"] = _clamp((spectral_base.get("score", 50)*0.3 + spec_synth.get("score", 50)*0.4 + vocoder_res.get("score", 50)*0.3))

    # Details
    details["f0"] = f0_res
    details["vtl"] = vtl_res
    details["mirroring"] = mirroring_res
    details["mfcc"] = mfcc_res
    details["spectral"] = {"detail": f"HPSS: {spec_synth.get('score', 0):.0f}, GAN: {vocoder_res.get('score', 0):.0f}"}
    details["breathing"] = breathing_res
    details["phase"] = phase_res

    # --- Signature 6/7: Network APIs ---
    hf_score = await _query_huggingface_audio(file_path)
    scores["hf"] = hf_score
    details["hf"] = {"score": hf_score, "detail": "wav2vec2-deepfake-transformer"}

    transcript = await _transcribe_with_groq(file_path)
    if transcript:
        groq_result = await _analyze_transcript_with_groq(transcript)
        scores["groq"] = groq_result.get("score", 50.0)
        details["groq"] = groq_result
    else:
        scores["groq"] = 50.0
        details["groq"] = {"score": 50.0, "analysis_summary": "No transcript available"}


    # ─── Step 3: AAS & Verdict ───
    aas_score = _compute_weighted_aas(scores)
    verdict = "LIKELY AI-GENERATED" if aas_score >= 70 else ("LIKELY REAL" if aas_score < 40 else "UNCERTAIN")

    # ─── Step 4: Findings ───
    findings_list = _generate_findings(scores, details)

    elapsed_ms = int((time.time() - start_time) * 1000)

    logger.info(
        f"AudioDetector DONE: AAS={aas_score:.1f} ({verdict}) "
        f"F0={scores['f0']:.0f} MFCC={scores['mfcc']:.0f} "
        f"Spectral={scores['spectral']:.0f} Breath={scores['breathing']:.0f} "
        f"Phase={scores['phase']:.0f} VTL={scores['vtl']:.0f} Mirror={scores['mirroring']:.0f} "
        f"HF={scores['hf']:.0f} Groq={scores['groq']:.0f} "
        f"in {elapsed_ms}ms"
    )
    
    return {
        "aas_score": aas_score,
        "verdict": verdict,
        "signature_scores": {k: round(v, 1) for k, v in scores.items()},
        "signature_details": details,
        "findings": findings_list,
        "spectrum": spectrum_data,
        "spectrogram_png": spectrogram_png,
        "anomalies": [], # Could be expanded
        "splicing_detected": breathing_res.get("silence_std_duration", 1) < 0.05,
        "clone_probability": round(aas_score, 1),
        "duration_seconds": round(duration, 2),
        "processing_time_ms": elapsed_ms,
    }


def _build_error_response(error_msg: str, elapsed: float) -> dict:
    """Build a safe error response dict matching the expected shape."""
    return {
        "aas_score": 50.0,
        "verdict": "UNCERTAIN",
        "signature_scores": {k: 50.0 for k in WEIGHTS},
        "signature_details": {},
        "findings": [f"Audio analysis error: {error_msg}"],
        "spectrum": [],
        "spectrogram_png": b"",
        "anomalies": [],
        "splicing_detected": False,
        "clone_probability": 50.0,
        "duration_seconds": 0.0,
        "processing_time_ms": int(elapsed * 1000),
    }


# =====================================================================
# Self-test
# =====================================================================
async def _self_test():
    """Generate a synthetic test signal and run the full pipeline."""
    import tempfile
    import soundfile as sf

    logger.info("AudioDetector SELF-TEST: Generating synthetic signal...")

    sr = 16000
    duration = 4.0  # seconds
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Synthetic voice-like signal: F0=200Hz + harmonics + noise
    signal = (
        0.5 * np.sin(2 * np.pi * 200 * t) +        # Fundamental
        0.3 * np.sin(2 * np.pi * 400 * t) +         # 2nd harmonic
        0.15 * np.sin(2 * np.pi * 600 * t) +        # 3rd harmonic
        0.05 * np.random.randn(len(t))               # Noise
    ).astype(np.float32)

    # Add a silence gap in the middle
    silence_start = int(1.8 * sr)
    silence_end = int(2.2 * sr)
    signal[silence_start:silence_end] *= 0.01

    # Write to temp file
    tmp_path = os.path.join(tempfile.gettempdir(), "deepscan_audio_selftest.wav")
    sf.write(tmp_path, signal, sr)

    try:
        result = await detect_audio(tmp_path)
        logger.info(f"SELF-TEST RESULT: AAS={result['aas_score']:.1f} — {result['verdict']}")
        logger.info(f"  Scores: {result['signature_scores']}")
        logger.info(f"  Findings: {result['findings'][:3]}")
        logger.info(f"  Spectrum points: {len(result['spectrum'])}")
        logger.info(f"  Spectrogram PNG bytes: {len(result['spectrogram_png'])}")
        logger.info(f"  Processing time: {result['processing_time_ms']}ms")
        return result
    finally:
        if os.path.exists(tmp_path):
            try:
                os.remove(tmp_path)
            except OSError:
                pass


# For backward compatibility: class wrapper matching old orchestrator interface
class AudioDetector:
    """Backward-compatible wrapper around the new detect_audio function.
    The orchestrator can instantiate this class and call analyze() or analyze_full()."""

    def __init__(self):
        logger.info("AudioDetector (7-signature) initialized")

    async def analyze(self, file_path: str) -> float:
        """Return just the AAS score 0-100."""
        result = await detect_audio(file_path)
        return result["aas_score"]

    async def analyze_full(self, file_path: str) -> dict:
        """Return full analysis result — compatible with orchestrator's _compute_aas."""
        result = await detect_audio(file_path)
        return {
            "score": result["aas_score"],
            "clone_probability": result["clone_probability"],
            "spectrum": result["spectrum"],
            "anomalies": result["anomalies"],
            "splicing_detected": result["splicing_detected"],
            # Extended data from 7-signature system
            "signature_scores": result["signature_scores"],
            "signature_details": result["signature_details"],
            "findings": result["findings"],
            "verdict": result["verdict"],
            "spectrogram_png": result.get("spectrogram_png", b""),
            "duration_seconds": result.get("duration_seconds", 0),
            "processing_time_ms": result.get("processing_time_ms", 0),
        }


if __name__ == "__main__":
    asyncio.run(_self_test())
