def calculate_aacs(mas: float, pps: float, irs: float, aas: float, cvs: float,
                   category: str = "unknown") -> float:
    """Calculate AACS using adaptive weights based on media type.
    
    For audio files, PPS (heartbeat) and CVS (reverse image search) are not
    applicable, so their weight is redistributed to the engines that ARE relevant.
    For images, PPS and AAS may not apply. For video, all engines apply.
    """
    # Base weights
    weights = {"mas": 0.30, "pps": 0.25, "irs": 0.20, "aas": 0.15, "cvs": 0.10}
    scores_map = {"mas": mas, "pps": pps, "irs": irs, "aas": aas, "cvs": cvs}

    # Determine which engines are applicable based on media category
    if category == "audio":
        # For audio: MAS (audio detector) and AAS (7-sig audio) are primary,
        # IRS (metadata) is secondary. PPS and CVS don't apply.
        applicable = {"mas", "aas", "irs"}
    elif category == "image":
        # For images: MAS (image detector), IRS (metadata), CVS (reverse search) apply.
        # PPS (heartbeat) and AAS (audio) don't apply.
        applicable = {"mas", "irs", "cvs"}
    elif category == "video":
        # All engines apply for video
        applicable = {"mas", "pps", "irs", "aas", "cvs"}
    else:
        applicable = {"mas", "pps", "irs", "aas", "cvs"}

    # Calculate with only applicable engines, redistributing weights
    total_weight = sum(weights[k] for k in applicable)
    if total_weight <= 0:
        return 50.0

    weighted_sum = 0.0
    for k in applicable:
        # Normalize weight so applicable weights sum to 1.0
        normalized_weight = weights[k] / total_weight
        weighted_sum += normalized_weight * scores_map[k]

    return max(0.0, min(100.0, weighted_sum))


def get_verdict(aacs: float) -> str:
    if aacs <= 30: return "AUTHENTIC"
    elif aacs <= 60: return "UNCERTAIN"
    elif aacs <= 85: return "LIKELY_FAKE"
    else: return "DEFINITELY_FAKE"

def get_verdict_color(verdict: str) -> str:
    return {"AUTHENTIC": "green", "UNCERTAIN": "yellow", "LIKELY_FAKE": "orange", "DEFINITELY_FAKE": "red"}.get(verdict, "gray")