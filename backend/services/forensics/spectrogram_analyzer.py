"""
spectrogram_analyzer.py — Deep spectrogram analysis for GAN vocoder fingerprints.

Two core functions:
1. analyze_spectrogram_for_synthesis — Full spectral texture analysis via HPSS + stats
2. check_for_gan_vocoder_patterns — Detect periodic artifacts from neural vocoders

Science Background:
    Neural vocoders (HiFi-GAN, WaveGlow, WaveNet, VITS) convert mel spectrograms
    back to waveforms. This process leaves telltale signatures:
    - Harmonic/percussive imbalance vs. real recordings
    - Periodic spectral ridges at GAN generator's stride frequency
    - Unusually smooth mel spectrogram texture (low variance across mel bins)
    - Missing or attenuated frequency components above training Nyquist
"""

import numpy as np
from loguru import logger

# Lazy imports
_librosa = None


def _get_librosa():
    global _librosa
    if _librosa is None:
        import librosa
        _librosa = librosa
    return _librosa


def analyze_spectrogram_for_synthesis(audio: np.ndarray, sr: int = 16000) -> dict:
    """Analyze mel spectrogram texture for signs of neural synthesis.

    Performs:
    1. Mel spectrogram computation (128 mel bands)
    2. Harmonic/Percussive Source Separation (HPSS)
    3. Spectral smoothness analysis (variance across time per mel band)
    4. High-frequency energy analysis (content near Nyquist)
    5. Temporal regularity check (frame-to-frame differences)

    Returns:
        dict with keys:
        - harmonic_ratio: fraction of energy that is harmonic (vs percussive)
        - spectral_smoothness: mean temporal variance per mel band (lower = smoother = more AI)
        - high_freq_energy_ratio: energy above 6kHz vs total
        - temporal_regularity: std of frame-to-frame mel differences (lower = more regular = more AI)
        - mel_variance_per_band: list of per-band variances (for visualization)
        - score: 0-100
    """
    librosa = _get_librosa()

    try:
        # --- Mel Spectrogram ---
        S = librosa.feature.melspectrogram(y=audio, sr=sr, n_mels=128, fmax=8000)
        S_dB = librosa.power_to_db(S, ref=np.max)

        # --- HPSS: Harmonic/Percussive separation ---
        D = librosa.stft(audio, n_fft=2048, hop_length=512)
        H, P = librosa.decompose.hpss(D, margin=3.0)
        harmonic_energy = float(np.sum(np.abs(H) ** 2))
        percussive_energy = float(np.sum(np.abs(P) ** 2))
        total_energy = harmonic_energy + percussive_energy
        harmonic_ratio = harmonic_energy / total_energy if total_energy > 0 else 0.5

        # --- Spectral smoothness (per-band temporal variance) ---
        # Low variance across time = smooth = vocoder-like
        band_variances = np.var(S_dB, axis=1)  # Variance across time for each mel band
        spectral_smoothness = float(np.mean(band_variances))

        # --- High-frequency energy ---
        # Neural vocoders trained at lower sample rates may lack high-freq content
        mel_freqs = librosa.mel_frequencies(n_mels=128, fmax=8000)
        high_mask = mel_freqs >= 6000
        high_freq_energy = float(np.sum(S[:, :][high_mask[: S.shape[0]], :]))
        total_mel_energy = float(np.sum(S))
        high_freq_ratio = high_freq_energy / total_mel_energy if total_mel_energy > 0 else 0.0

        # --- Temporal regularity ---
        # Frame-to-frame differences in mel spectrogram
        frame_diffs = np.diff(S_dB, axis=1)
        temporal_regularity = float(np.std(np.mean(np.abs(frame_diffs), axis=0)))

    except Exception as e:
        logger.warning(f"analyze_spectrogram_for_synthesis failed: {e}")
        return {
            "harmonic_ratio": 0.5, "spectral_smoothness": 0.0,
            "high_freq_energy_ratio": 0.0, "temporal_regularity": 0.0,
            "mel_variance_per_band": [], "score": 50.0,
        }

    # --- Scoring ---
    score = 50.0

    # High harmonic ratio → may indicate synthetic harmonics from vocoder
    if harmonic_ratio > 0.92:
        score += 15  # Abnormally harmonic
    elif harmonic_ratio > 0.85:
        score += 8
    elif harmonic_ratio < 0.6:
        score -= 10  # Natural mix of harmonic and percussive

    # Low spectral smoothness → smoother mel bands → vocoder artifact
    if spectral_smoothness < 30:
        score += 18
    elif spectral_smoothness < 60:
        score += 8
    elif spectral_smoothness > 120:
        score -= 10

    # Very low high-frequency content → vocoder bandwidth limitation
    if high_freq_ratio < 0.001:
        score += 12
    elif high_freq_ratio < 0.01:
        score += 5
    elif high_freq_ratio > 0.05:
        score -= 5

    # Low temporal regularity → too predictable frame transitions
    if temporal_regularity < 1.5:
        score += 12
    elif temporal_regularity < 3.0:
        score += 5
    elif temporal_regularity > 8.0:
        score -= 8

    return {
        "harmonic_ratio": round(harmonic_ratio, 4),
        "spectral_smoothness": round(spectral_smoothness, 3),
        "high_freq_energy_ratio": round(high_freq_ratio, 5),
        "temporal_regularity": round(temporal_regularity, 4),
        "mel_variance_per_band": band_variances.tolist()[:128] if band_variances is not None else [],
        "score": round(min(100, max(0, score)), 1),
    }


def check_for_gan_vocoder_patterns(audio: np.ndarray, sr: int = 16000) -> dict:
    """Check for periodic artifacts typical of GAN-based vocoders.

    Science: GAN vocoders (HiFi-GAN, MelGAN, Parallel WaveGAN) use
    upsampling layers with fixed stride. This creates periodic ridges
    in the spectrogram at multiples of the generator's fundamental
    upsampling frequency. These appear as:
    - Regular spectral peaks in the autocorrelation of the magnitude spectrum
    - Periodic energy bumps when analyzing the power spectrum along frequency

    Returns:
        dict with keys:
        - has_periodic_artifacts: bool
        - artifact_frequencies: list of detected artifact frequencies
        - periodicity_strength: 0-1 measure of how periodic the spectrum is
        - autocorr_peak_ratio: ratio of strongest autocorrelation peak to mean
        - score: 0-100
    """
    librosa = _get_librosa()
    from scipy.fft import rfft, rfftfreq

    try:
        # Compute magnitude spectrogram
        D = librosa.stft(audio, n_fft=4096, hop_length=512)
        mag = np.abs(D)

        # Average magnitude across time → spectrum profile
        avg_spectrum = np.mean(mag, axis=1)

        # Compute autocorrelation of the average spectrum
        # To find periodic ridges
        autocorr = np.correlate(avg_spectrum - np.mean(avg_spectrum),
                                avg_spectrum - np.mean(avg_spectrum), mode="full")
        autocorr = autocorr[len(autocorr) // 2:]  # Take positive lags only
        if np.max(np.abs(autocorr)) > 0:
            autocorr = autocorr / autocorr[0]  # Normalize

        # Find peaks in autocorrelation (excluding lag 0)
        from scipy.signal import find_peaks
        peaks, properties = find_peaks(autocorr[1:], height=0.15, distance=5)
        peak_heights = properties["peak_heights"] if len(peaks) > 0 else np.array([])

        # --- Artifact detection ---
        has_artifacts = len(peaks) >= 3  # Multiple periodic peaks = vocoder fingerprint
        autocorr_peak_ratio = float(np.max(peak_heights)) if len(peak_heights) > 0 else 0.0

        # Map peaks back to frequencies
        freq_resolution = sr / 4096
        artifact_freqs = [(int(p) * freq_resolution) for p in peaks[:5]]

        # Periodicity strength: how dominant are the periodic components
        periodicity_strength = float(np.mean(peak_heights)) if len(peak_heights) > 0 else 0.0

    except Exception as e:
        logger.warning(f"check_for_gan_vocoder_patterns failed: {e}")
        return {
            "has_periodic_artifacts": False,
            "artifact_frequencies": [],
            "periodicity_strength": 0.0,
            "autocorr_peak_ratio": 0.0,
            "score": 50.0,
        }

    # --- Scoring ---
    if has_artifacts and autocorr_peak_ratio > 0.5:
        score = 88.0  # Strong periodic artifacts → very likely vocoder
    elif has_artifacts and autocorr_peak_ratio > 0.3:
        score = 70.0
    elif has_artifacts:
        score = 55.0
    elif periodicity_strength > 0.2:
        score = 45.0
    else:
        score = 18.0  # No periodic artifacts → likely real

    return {
        "has_periodic_artifacts": has_artifacts,
        "artifact_frequencies": [round(f, 1) for f in artifact_freqs],
        "periodicity_strength": round(periodicity_strength, 4),
        "autocorr_peak_ratio": round(autocorr_peak_ratio, 4),
        "score": round(min(100, max(0, score)), 1),
    }
