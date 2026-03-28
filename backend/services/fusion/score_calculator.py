"""
score_calculator.py — Bulletproof AACS Score Calculator

Handles None/NaN/missing sub-scores by redistributing weights
to present detectors. NEVER returns NaN. NEVER crashes.
"""
import math
from loguru import logger


def calculate_aacs(scores: dict = None, mas: float = None, pps: float = None,
                   irs: float = None, aas: float = None, cvs: float = None,
                   category: str = "unknown") -> dict:
    """Calculate AACS with bulletproof handling of missing/failed detectors.

    Accepts EITHER a scores dict OR individual keyword arguments for
    backward compatibility with the existing orchestrator.

    Returns a rich result dict (never crashes, never returns NaN).
    """
    # Normalize input: support both dict and kwargs
    if scores is None:
        scores = {}
    raw = {
        "MAS": scores.get("MAS", scores.get("mas", mas)),
        "PPS": scores.get("PPS", scores.get("pps", pps)),
        "IRS": scores.get("IRS", scores.get("irs", irs)),
        "AAS": scores.get("AAS", scores.get("aas", aas)),
        "CVS": scores.get("CVS", scores.get("cvs", cvs)),
    }

    # Base weights per category — primary detector gets strong weight
    if category == "audio":
        weights = {"MAS": 0.50, "AAS": 0.40, "IRS": 0.10, "PPS": 0.00, "CVS": 0.00}
    elif category == "image":
        weights = {"MAS": 0.60, "IRS": 0.25, "CVS": 0.15, "PPS": 0.00, "AAS": 0.00}
    elif category == "video":
        weights = {"MAS": 0.35, "PPS": 0.20, "IRS": 0.15, "AAS": 0.15, "CVS": 0.15}
    else:
        weights = {"MAS": 0.30, "PPS": 0.25, "IRS": 0.20, "AAS": 0.15, "CVS": 0.10}

    # Step 1: Clean and clamp — replace None/NaN with None marker
    clean = {}
    for key in weights:
        val = raw.get(key)
        if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
            clean[key] = None  # will redistribute
        else:
            clean[key] = max(0.0, min(100.0, float(val)))

    # Step 2: Identify present keys (with non-zero weight)
    present_keys = [k for k in weights if clean[k] is not None and weights[k] > 0]

    if not present_keys:
        # ALL detectors failed — return honest uncertain score
        return {
            "aacs": 50.0,
            "verdict": "Uncertain",
            "confidence": 0.0,
            "sub_scores": {k: None for k in weights},
            "detectors_used": [],
            "fallback_used": True,
            "warning": "All detectors failed — heuristic fallback"
        }

    # Step 3: Redistribute missing weight proportionally
    total_present_weight = sum(weights[k] for k in present_keys)
    missing_weight = sum(w for k, w in weights.items() if clean[k] is None or weights[k] == 0)

    adjusted_weights = {}
    for k in present_keys:
        adjusted_weights[k] = weights[k] + (weights[k] / total_present_weight * missing_weight)

    # Step 4: Calculate AACS
    weighted_sum = sum(clean[k] * adjusted_weights[k] for k in present_keys)

    # Confidence boost: if ALL applicable engines agree strongly (>70 or <25), amplify
    vals = [clean[k] for k in present_keys]
    if all(v >= 70 for v in vals):
        weighted_sum = min(100.0, weighted_sum * 1.10)
    elif all(v <= 25 for v in vals):
        weighted_sum = max(0.0, weighted_sum * 0.90)

    aacs = max(0.0, min(100.0, round(weighted_sum, 2)))

    # Step 5: Verdict bands
    verdict = get_verdict(aacs)

    return {
        "aacs": aacs,
        "verdict": verdict,
        "confidence": round(total_present_weight, 2),
        "sub_scores": {k: round(clean[k], 2) if clean[k] is not None else None for k in weights},
        "detectors_used": present_keys,
        "fallback_used": len(present_keys) < sum(1 for w in weights.values() if w > 0),
    }


def get_verdict(aacs: float) -> str:
    """Map AACS 0-100 to verdict string. Never crashes."""
    try:
        aacs = float(aacs)
    except (TypeError, ValueError):
        return "Uncertain"
    if aacs <= 30:
        return "Authentic"
    elif aacs <= 60:
        return "Uncertain"
    elif aacs <= 85:
        return "Likely Fake"
    else:
        return "Definitely Fake"


def get_verdict_color(verdict: str) -> str:
    return {
        "Authentic": "green", "AUTHENTIC": "green",
        "Uncertain": "yellow", "UNCERTAIN": "yellow",
        "Likely Fake": "orange", "LIKELY_FAKE": "orange",
        "Definitely Fake": "red", "DEFINITELY_FAKE": "red",
    }.get(verdict, "gray")