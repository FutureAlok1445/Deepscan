"""
audio_utils.py — Low-level audio feature extraction for deepfake detection.

8 core functions that power the 7-signature audio analysis:
1. load_audio           — Load any audio/video → mono float32 numpy array
2. extract_f0           — Fundamental frequency (F0) via pYIN
3. extract_mfcc_features — MFCC deltas + delta-deltas
4. extract_spectral_features — Spectral centroid, bandwidth, rolloff, contrast, flatness
5. analyze_silence_breathing — Breathing / silence band energy via FFT
6. compute_phase_features — STFT phase discontinuity detection
7. generate_spectrogram_image — Mel spectrogram → PNG bytes for explainability
8. get_audio_duration   — Duration in seconds
"""

import os
import io
import subprocess
import tempfile
import numpy as np
import soundfile as sf
from scipy import signal as scipy_signal
from loguru import logger

# ------------------------------------------------------------------
# Lazy imports (expensive modules loaded on first call)
# ------------------------------------------------------------------
_librosa = None
_plt = None


def _get_librosa():
    global _librosa
    if _librosa is None:
        import librosa
        _librosa = librosa
    return _librosa


def _get_plt():
    global _plt
    if _plt is None:
        import matplotlib
        matplotlib.use("Agg")  # Non-interactive backend
        import matplotlib.pyplot as plt
        _plt = plt
    return _plt


# ==================================================================
# 1. load_audio
# ==================================================================
def load_audio(file_path: str, sr: int = 16000) -> tuple:
    """Load any audio/video file → (samples: np.ndarray float32, sample_rate: int).

    Strategy chain:
      1. Try soundfile (fast, supports WAV/FLAC/OGG)
      2. Try librosa (handles MP3, M4A via audioread)
      3. Fall back to ffmpeg subprocess → WAV temp file → soundfile

    Always returns mono, resampled to `sr`.
    """
    audio = None
    actual_sr = sr

    # --- Strategy 1: soundfile (fast C library) ---
    try:
        audio, actual_sr = sf.read(file_path, dtype="float32")
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        logger.debug(f"audio_utils.load_audio: soundfile OK  sr={actual_sr}  len={len(audio)}")
    except Exception as e:
        logger.debug(f"audio_utils.load_audio: soundfile failed ({e}), trying librosa")
        audio = None

    # --- Strategy 2: librosa (audioread handles mp3/m4a) ---
    if audio is None:
        try:
            librosa = _get_librosa()
            audio, actual_sr = librosa.load(file_path, sr=sr, mono=True)
            logger.debug(f"audio_utils.load_audio: librosa OK  sr={actual_sr}  len={len(audio)}")
        except Exception as e:
            logger.debug(f"audio_utils.load_audio: librosa failed ({e}), trying ffmpeg")
            audio = None

    # --- Strategy 3: ffmpeg subprocess → temp WAV → soundfile ---
    if audio is None:
        tmp_wav = os.path.join(
            tempfile.gettempdir(), f"deepscan_audio_{os.getpid()}.wav"
        )
        try:
            subprocess.run(
                [
                    "ffmpeg", "-y", "-i", file_path,
                    "-vn",                        # strip video
                    "-acodec", "pcm_s16le",       # 16-bit PCM
                    "-ar", str(sr),               # target sample rate
                    "-ac", "1",                   # mono
                    tmp_wav,
                ],
                check=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            audio, actual_sr = sf.read(tmp_wav, dtype="float32")
            if audio.ndim > 1:
                audio = np.mean(audio, axis=1)
            logger.debug(f"audio_utils.load_audio: ffmpeg OK  sr={actual_sr}  len={len(audio)}")
        except Exception as e:
            logger.error(f"audio_utils.load_audio: ALL strategies failed for {file_path}: {e}")
            raise RuntimeError(f"Cannot load audio from {file_path}: {e}")
        finally:
            if os.path.exists(tmp_wav):
                try:
                    os.remove(tmp_wav)
                except OSError:
                    pass

    # --- Resample to target sr if needed ---
    if actual_sr != sr and audio is not None and len(audio) > 0:
        num_samples = int(len(audio) * sr / actual_sr)
        if num_samples > 0:
            audio = scipy_signal.resample(audio, num_samples).astype(np.float32)
        actual_sr = sr

    # Ensure float32
    audio = np.asarray(audio, dtype=np.float32)
    return audio, actual_sr


# ==================================================================
# 2. extract_f0 — Fundamental Frequency via pYIN
# ==================================================================
def extract_f0(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract F0 trajectory using librosa.pyin.

    Science: Real human voices have natural micro-variations in pitch (jitter).
    AI-generated voices from TTS/vocoders produce unnaturally stable F0 contours
    because they synthesize pitch from smooth parametric curves.

    Returns:
        dict with keys:
        - f0_mean, f0_std, f0_range: basic stats (Hz)
        - f0_stability: coefficient of variation (std/mean) — lower = more stable = more suspicious
        - voiced_fraction: what fraction of frames are voiced
        - f0_values: list of non-NaN F0 values for plotting
        - jitter: mean absolute difference between consecutive F0 values
        - score: 0-100 where 100 = definitely AI (unnaturally stable)
    """
    librosa = _get_librosa()

    try:
        f0, voiced_flag, voiced_probs = librosa.pyin(
            audio, fmin=50, fmax=550, sr=sr, frame_length=2048
        )
    except Exception as e:
        logger.warning(f"extract_f0 failed: {e}")
        return {
            "f0_mean": 0.0, "f0_std": 0.0, "f0_range": 0.0,
            "f0_stability": 0.0, "voiced_fraction": 0.0,
            "f0_values": [], "jitter": 0.0, "score": 50.0,
        }

    # Filter NaN (unvoiced frames)
    valid_f0 = f0[~np.isnan(f0)]
    total_frames = len(f0)
    voiced_count = len(valid_f0)

    if voiced_count < 5:
        return {
            "f0_mean": 0.0, "f0_std": 0.0, "f0_range": 0.0,
            "f0_stability": 0.0, "voiced_fraction": 0.0,
            "f0_values": [], "jitter": 0.0, "score": 50.0,
        }

    f0_mean = float(np.mean(valid_f0))
    f0_std = float(np.std(valid_f0))
    f0_range = float(np.ptp(valid_f0))
    voiced_fraction = voiced_count / total_frames if total_frames > 0 else 0.0
    f0_stability = f0_std / f0_mean if f0_mean > 0 else 0.0

    # Jitter: mean absolute consecutive F0 difference (normalized by mean F0)
    jitter = float(np.mean(np.abs(np.diff(valid_f0)))) / f0_mean if f0_mean > 0 else 0.0

    # --- Scoring ---
    # Very stable F0 (low CoV) → suspicious
    # Real speech: CoV typically 0.10–0.30
    # AI speech: CoV often < 0.05
    if f0_stability < 0.03:
        score = 90.0   # Extremely stable — almost certainly synthetic
    elif f0_stability < 0.06:
        score = 75.0   # Very stable — likely synthetic
    elif f0_stability < 0.10:
        score = 55.0   # Somewhat stable — ambiguous
    elif f0_stability < 0.20:
        score = 30.0   # Normal variation — likely real
    else:
        score = 10.0   # High variation — very likely real

    # Adjust for jitter: low jitter also suspicious
    if jitter < 0.005:
        score = min(100, score + 15)
    elif jitter < 0.01:
        score = min(100, score + 8)
    elif jitter > 0.04:
        score = max(0, score - 10)

    return {
        "f0_mean": round(f0_mean, 2),
        "f0_std": round(f0_std, 3),
        "f0_range": round(f0_range, 2),
        "f0_stability": round(f0_stability, 4),
        "voiced_fraction": round(voiced_fraction, 3),
        "f0_values": valid_f0.tolist()[:200],  # Cap for JSON size
        "jitter": round(jitter, 5),
        "score": round(min(100, max(0, score)), 1),
    }


# ==================================================================
# 3. extract_mfcc_features — MFCC delta variance analysis
# ==================================================================
def extract_mfcc_features(audio: np.ndarray, sr: int = 16000, n_mfcc: int = 13) -> dict:
    """Extract MFCCs, deltas, and delta-deltas.

    Science: MFCCs capture the spectral envelope (vocal tract shape).
    Delta-MFCCs capture how the vocal tract changes over time.
    Real speech has rich, varied delta patterns because articulators
    (tongue, lips, jaw) move organically. AI vocoders produce
    smoother, more regular delta patterns.

    Returns:
        dict with keys:
        - mfcc_mean: list of mean values per coefficient
        - delta_var: mean variance of delta-MFCCs (lower = more suspicious)
        - delta2_var: mean variance of delta-delta-MFCCs
        - delta_range: mean range of delta-MFCCs
        - score: 0-100 where 100 = definitely AI
    """
    librosa = _get_librosa()

    try:
        mfccs = librosa.feature.mfcc(y=audio, sr=sr, n_mfcc=n_mfcc)
        delta = librosa.feature.delta(mfccs, order=1)
        delta2 = librosa.feature.delta(mfccs, order=2)
    except Exception as e:
        logger.warning(f"extract_mfcc_features failed: {e}")
        return {
            "mfcc_mean": [], "delta_var": 0.0, "delta2_var": 0.0,
            "delta_range": 0.0, "score": 50.0,
        }

    mfcc_mean = np.mean(mfccs, axis=1).tolist()
    delta_var = float(np.mean(np.var(delta, axis=1)))
    delta2_var = float(np.mean(np.var(delta2, axis=1)))
    delta_range = float(np.mean(np.ptp(delta, axis=1)))

    # --- Scoring ---
    # Low delta variance → smoother transitions → more AI-like
    # Real speech typically: delta_var > 10
    # AI speech typically: delta_var < 5
    if delta_var < 2.0:
        score = 90.0
    elif delta_var < 5.0:
        score = 72.0
    elif delta_var < 10.0:
        score = 50.0
    elif delta_var < 20.0:
        score = 28.0
    else:
        score = 10.0

    # Cross-check with delta2 (acceleration)
    if delta2_var < 1.0:
        score = min(100, score + 12)
    elif delta2_var < 3.0:
        score = min(100, score + 5)
    elif delta2_var > 15.0:
        score = max(0, score - 8)

    return {
        "mfcc_mean": [round(v, 3) for v in mfcc_mean],
        "delta_var": round(delta_var, 4),
        "delta2_var": round(delta2_var, 4),
        "delta_range": round(delta_range, 4),
        "score": round(min(100, max(0, score)), 1),
    }


# ==================================================================
# 4. extract_spectral_features
# ==================================================================
def extract_spectral_features(audio: np.ndarray, sr: int = 16000) -> dict:
    """Extract spectral texture features.

    Science: Neural vocoders (WaveNet, HiFi-GAN, VITS) generate audio via
    learned spectral distributions. Their output often has:
    - Unusually uniform spectral flatness (more noise-like)
    - Narrow spectral bandwidth vs. real recordings
    - Missing or reduced high-frequency content above the Nyquist
      of the training data

    Returns:
        dict with keys:
        - centroid_mean, centroid_std: spectral centroid stats (Hz)
        - bandwidth_mean: spectral bandwidth
        - rolloff_mean: frequency below which 85% energy resides
        - contrast_mean: spectral contrast (energy difference between peaks & valleys)
        - flatness_mean: spectral flatness (0 = tonal, 1 = white noise)
        - score: 0-100
    """
    librosa = _get_librosa()

    try:
        centroid = librosa.feature.spectral_centroid(y=audio, sr=sr)[0]
        bandwidth = librosa.feature.spectral_bandwidth(y=audio, sr=sr)[0]
        rolloff = librosa.feature.spectral_rolloff(y=audio, sr=sr, roll_percent=0.85)[0]
        contrast = librosa.feature.spectral_contrast(y=audio, sr=sr)
        flatness = librosa.feature.spectral_flatness(y=audio)[0]
    except Exception as e:
        logger.warning(f"extract_spectral_features failed: {e}")
        return {
            "centroid_mean": 0.0, "centroid_std": 0.0,
            "bandwidth_mean": 0.0, "rolloff_mean": 0.0,
            "contrast_mean": 0.0, "flatness_mean": 0.0,
            "score": 50.0,
        }

    centroid_mean = float(np.mean(centroid))
    centroid_std = float(np.std(centroid))
    bandwidth_mean = float(np.mean(bandwidth))
    rolloff_mean = float(np.mean(rolloff))
    contrast_mean = float(np.mean(contrast))
    flatness_mean = float(np.mean(flatness))

    # --- Scoring ---
    score = 50.0  # Start neutral

    # High flatness = noise-like spectrum → suspicious for voice
    if flatness_mean > 0.4:
        score += 20
    elif flatness_mean > 0.25:
        score += 10
    elif flatness_mean < 0.05:
        score -= 10

    # Low spectral bandwidth → narrow frequency range → vocoder artifact
    if bandwidth_mean < 1500:
        score += 15
    elif bandwidth_mean < 2000:
        score += 8
    elif bandwidth_mean > 3500:
        score -= 10

    # Low spectral contrast → flat energy → vocoder-like
    if contrast_mean < 15:
        score += 12
    elif contrast_mean < 20:
        score += 5
    elif contrast_mean > 30:
        score -= 8

    # If centroid is unusually stable (low std) → synthetic
    cv = centroid_std / centroid_mean if centroid_mean > 0 else 0
    if cv < 0.15:
        score += 10
    elif cv > 0.4:
        score -= 5

    return {
        "centroid_mean": round(centroid_mean, 2),
        "centroid_std": round(centroid_std, 2),
        "bandwidth_mean": round(bandwidth_mean, 2),
        "rolloff_mean": round(rolloff_mean, 2),
        "contrast_mean": round(contrast_mean, 3),
        "flatness_mean": round(flatness_mean, 5),
        "score": round(min(100, max(0, score)), 1),
    }


# ==================================================================
# 5. analyze_silence_breathing — Breathing / micro-silence analysis
# ==================================================================
def analyze_silence_breathing(audio: np.ndarray, sr: int = 16000) -> dict:
    """Analyze silence patterns and breathing band energy.

    Science: Real speech has natural micro-pauses, breathing sounds
    between phrases, and variable silence lengths. AI-generated audio
    often has:
    - Perfectly regular silence gaps (same duration each time)
    - Missing breathing sounds in pauses
    - Unnatural fade-in/fade-out at segment boundaries

    Returns dict with:
    - silence_count: number of silence segments detected
    - silence_mean_duration: average silence length (seconds)
    - silence_std_duration: std dev of silence lengths (low = suspicious)
    - breathing_energy_ratio: energy in breathing band (0.1–0.5 kHz) vs total
    - has_natural_breathing: bool
    - score: 0-100
    """
    librosa = _get_librosa()
    from scipy.fft import rfft, rfftfreq

    try:
        # Detect non-silent intervals using librosa
        intervals = librosa.effects.split(audio, top_db=30, frame_length=2048, hop_length=512)
    except Exception as e:
        logger.warning(f"analyze_silence_breathing: split failed: {e}")
        intervals = np.array([])

    total_samples = len(audio)
    duration = total_samples / sr if sr > 0 else 0

    # Compute silence segments (gaps between voiced intervals)
    silence_durations = []
    if len(intervals) > 1:
        for i in range(1, len(intervals)):
            gap_start = intervals[i - 1][1]
            gap_end = intervals[i][0]
            gap_dur = (gap_end - gap_start) / sr
            if gap_dur > 0.01:  # Ignore tiny gaps
                silence_durations.append(gap_dur)

    silence_count = len(silence_durations)
    silence_mean = float(np.mean(silence_durations)) if silence_durations else 0.0
    silence_std = float(np.std(silence_durations)) if len(silence_durations) > 1 else 0.0

    # --- Breathing band energy analysis ---
    # Breathing sounds concentrate in 100–500 Hz with low amplitude
    has_natural_breathing = False
    breathing_ratio = 0.0

    if total_samples > 1024:
        try:
            yf = rfft(audio)
            xf = rfftfreq(total_samples, 1.0 / sr)
            magnitude = np.abs(yf)

            # Breathing band: 100-500 Hz
            breath_mask = (xf >= 100) & (xf <= 500)
            total_energy = np.sum(magnitude ** 2)
            breath_energy = np.sum(magnitude[breath_mask] ** 2) if np.any(breath_mask) else 0.0
            breathing_ratio = float(breath_energy / total_energy) if total_energy > 0 else 0.0

            # Real breathing typically contributes 5-15% of total energy in speech
            has_natural_breathing = 0.03 < breathing_ratio < 0.25
        except Exception as e:
            logger.debug(f"Breathing energy analysis failed: {e}")

    # --- Scoring ---
    score = 50.0

    # No silences at all in speech > 2 seconds → suspicious
    if duration > 2.0 and silence_count == 0:
        score += 20

    # Very regular silence patterns (low std)
    if silence_count > 2 and silence_std < 0.02:
        score += 20  # Robotically regular pauses
    elif silence_count > 2 and silence_std < 0.05:
        score += 10

    # No natural breathing sounds
    if not has_natural_breathing and duration > 3.0:
        score += 15

    # Breathing too uniform or absent
    if breathing_ratio < 0.01 and duration > 2.0:
        score += 10
    elif breathing_ratio > 0.05:
        score -= 10  # Has natural breathing energy

    # Natural irregularity bonus
    if silence_count > 3 and silence_std > 0.15:
        score -= 15  # Irregular pauses = more natural

    return {
        "silence_count": silence_count,
        "silence_mean_duration": round(silence_mean, 4),
        "silence_std_duration": round(silence_std, 4),
        "breathing_energy_ratio": round(breathing_ratio, 5),
        "has_natural_breathing": has_natural_breathing,
        "score": round(min(100, max(0, score)), 1),
    }


# ==================================================================
# 6. compute_phase_features — Phase discontinuity detection
# ==================================================================
def compute_phase_features(audio: np.ndarray, sr: int = 16000) -> dict:
    """Analyze STFT phase for discontinuities.

    Science: Neural vocoders often use a mel spectrogram → waveform
    pipeline that reconstructs phase using Griffin-Lim or learned
    phase prediction. This produces subtle phase discontinuities at
    frame boundaries — the phase "jumps" instead of flowing smoothly.
    Real audio recorded by a microphone has naturally continuous phase
    progression governed by the physics of sound waves.

    Returns dict with:
    - phase_diff_mean: mean absolute instantaneous phase derivative
    - phase_diff_std: std of phase differences
    - discontinuity_count: frames with phase jumps > threshold
    - discontinuity_ratio: fraction of frames with discontinuities
    - score: 0-100
    """
    librosa = _get_librosa()

    try:
        # Short-time Fourier Transform
        stft = librosa.stft(audio, n_fft=2048, hop_length=512)
        phase = np.angle(stft)

        # Instantaneous frequency (phase derivative across time)
        inst_freq = np.diff(phase, axis=1)

        # Wrap to [-pi, pi]
        inst_freq = np.angle(np.exp(1j * inst_freq))

        # Compute statistics across frequency bins
        phase_diff_mean = float(np.mean(np.abs(inst_freq)))
        phase_diff_std = float(np.std(np.abs(inst_freq)))

        # Detect discontinuities: frames where phase jumps > 2.5 radians
        threshold = 2.5
        jumps = np.abs(inst_freq) > threshold
        discontinuity_count = int(np.sum(np.any(jumps, axis=0)))  # frames with any jump
        total_frames = inst_freq.shape[1]
        discontinuity_ratio = discontinuity_count / total_frames if total_frames > 0 else 0.0

    except Exception as e:
        logger.warning(f"compute_phase_features failed: {e}")
        return {
            "phase_diff_mean": 0.0, "phase_diff_std": 0.0,
            "discontinuity_count": 0, "discontinuity_ratio": 0.0,
            "score": 50.0,
        }

    # --- Scoring ---
    # High discontinuity ratio → more phase jumps → more likely vocoder output
    if discontinuity_ratio > 0.4:
        score = 85.0
    elif discontinuity_ratio > 0.25:
        score = 68.0
    elif discontinuity_ratio > 0.15:
        score = 50.0
    elif discontinuity_ratio > 0.08:
        score = 32.0
    else:
        score = 15.0

    # Cross-check with phase diff statistics
    # Vocoders tend to have more uniform phase diffs (lower std)
    if phase_diff_std < 0.5 and discontinuity_ratio > 0.1:
        score = min(100, score + 10)

    return {
        "phase_diff_mean": round(phase_diff_mean, 4),
        "phase_diff_std": round(phase_diff_std, 4),
        "discontinuity_count": discontinuity_count,
        "discontinuity_ratio": round(discontinuity_ratio, 4),
        "score": round(min(100, max(0, score)), 1),
    }


# ==================================================================
# 7. generate_spectrogram_image — Mel spectrogram → PNG bytes
# ==================================================================
def generate_spectrogram_image(audio: np.ndarray, sr: int = 16000) -> bytes:
    """Generate a mel spectrogram image as PNG bytes.

    Used for:
    - Visual explainability (shown to users)
    - Input to spectrogram texture analysis
    - GradCAM-like overlay for audio

    Returns:
        PNG image bytes (or empty bytes on failure)
    """
    librosa = _get_librosa()
    plt = _get_plt()

    try:
        S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
        S_dB = librosa.power_to_db(S, ref=np.max)

        fig, ax = plt.subplots(1, 1, figsize=(10, 4), dpi=100)
        img = ax.imshow(
            S_dB, aspect="auto", origin="lower",
            extent=[0, len(audio) / sr, 0, sr / 2],
            cmap="magma",
        )
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Frequency (Hz)")
        ax.set_title("Mel Spectrogram")
        fig.colorbar(img, ax=ax, format="%+2.0f dB")
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format="png", bbox_inches="tight")
        plt.close(fig)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        logger.warning(f"generate_spectrogram_image failed: {e}")
        return b""


# ==================================================================
# 8. get_audio_duration
# ==================================================================
def get_audio_duration(file_path: str) -> float:
    """Return audio duration in seconds. Fast path via soundfile, fallback via librosa."""
    try:
        info = sf.info(file_path)
        return float(info.duration)
    except Exception:
        pass

    try:
        librosa = _get_librosa()
        return float(librosa.get_duration(path=file_path))
    except Exception:
        pass

    return 0.0


# ==================================================================
# Legacy helper (kept for backward compatibility)
# ==================================================================
def extract_audio_from_video(video: str, out: str) -> bool:
    """Extract audio track from video file using ffmpeg."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", video, "-vn", "-acodec", "pcm_s16le",
             "-ar", "16000", "-ac", "1", out],
            check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        return os.path.exists(out)
    except Exception:
        return False