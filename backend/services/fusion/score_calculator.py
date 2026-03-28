def calculate_aacs(mas: float, pps: float, irs: float, aas: float, cvs: float,
                   category: str = "unknown") -> float:
    """Calculate AACS using adaptive weights based on media type.
    
    For audio files, PPS (heartbeat) and CVS (reverse image search) are not
    applicable, so their weight is redistributed to the engines that ARE relevant.
    For images, PPS and AAS may not apply. For video, all engines apply.
    
    The primary detector (MAS) always gets the highest weight. When both MAS and
    AAS point the same direction for audio, confidence is maximal.
    """
    # Base weights per category — primary detector gets strong weight
    if category == "audio":
        # Audio: MAS + AAS both run 7-sig. Give heavy weight to detection.
        # IRS only catches metadata issues (usually 0 for clean files)
        weights = {"mas": 0.50, "aas": 0.40, "irs": 0.10}
        scores_map = {"mas": mas, "aas": aas, "irs": irs}
    elif category == "image":
        # Image: MAS (ViT) is primary, IRS (metadata) secondary, CVS (reverse search) tertiary
        weights = {"mas": 0.60, "irs": 0.25, "cvs": 0.15}
        scores_map = {"mas": mas, "irs": irs, "cvs": cvs}
    elif category == "video":
        # Video: all 5 engines, MAS dominates
        weights = {"mas": 0.35, "pps": 0.20, "irs": 0.15, "aas": 0.15, "cvs": 0.15}
        scores_map = {"mas": mas, "pps": pps, "irs": irs, "aas": aas, "cvs": cvs}
    else:
        weights = {"mas": 0.30, "pps": 0.25, "irs": 0.20, "aas": 0.15, "cvs": 0.10}
        scores_map = {"mas": mas, "pps": pps, "irs": irs, "aas": aas, "cvs": cvs}

    # Weighted sum (weights already sum to ~1.0 per category)
    total_weight = sum(weights.values())
    weighted_sum = sum((w / total_weight) * scores_map[k] for k, w in weights.items())

    # Confidence boost: if ALL applicable engines agree strongly (>70 or <25), amplify signal
    vals = list(scores_map.values())
    if all(v >= 70 for v in vals if v > 0):
        # All engines say fake — boost by 10%
        weighted_sum = min(100.0, weighted_sum * 1.10)
    elif all(v <= 25 for v in vals):
        # All engines say real — push toward authentic
        weighted_sum = max(0.0, weighted_sum * 0.90)

    return max(0.0, min(100.0, round(weighted_sum, 2)))


def get_verdict(aacs: float) -> str:
    if aacs <= 34: return "AUTHENTIC"
    elif aacs <= 70: return "PARTIALLY_AI"
    elif aacs <= 85: return "LIKELY_FAKE"
    else: return "DEFINITELY_FAKE"

def get_verdict_color(verdict: str) -> str:
    return {"AUTHENTIC": "green", "PARTIALLY_AI": "yellow", "LIKELY_FAKE": "orange", "DEFINITELY_FAKE": "red"}.get(verdict, "gray")