from loguru import logger

try:
    from scipy.signal import butter, filtfilt
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False
    logger.warning("scipy not installed — signal filtering will return raw data")


def butter_bandpass(lowcut, highcut, fs, order=5):
    return butter(order, [lowcut / (0.5 * fs), highcut / (0.5 * fs)], btype='band')


def apply_filter(data, fs=30.0, lowcut=0.7, highcut=4.0):
    if not HAS_SCIPY:
        return data  # return unfiltered signal as fallback
    b, a = butter_bandpass(lowcut, highcut, fs)
    return filtfilt(b, a, data)