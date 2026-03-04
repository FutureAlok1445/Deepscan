def calculate_aacs(mas: float, pps: float, irs: float, aas: float, cvs: float) -> float:
    return max(0.0, min(100.0, (0.30 * mas) + (0.25 * pps) + (0.20 * irs) + (0.15 * aas) + (0.10 * cvs)))

def get_verdict(aacs: float) -> str:
    if aacs <= 30: return "AUTHENTIC"
    elif aacs <= 60: return "UNCERTAIN"
    elif aacs <= 85: return "LIKELY_FAKE"
    else: return "DEFINITELY_FAKE"

def get_verdict_color(verdict: str) -> str:
    return {"AUTHENTIC": "green", "UNCERTAIN": "yellow", "LIKELY_FAKE": "orange", "DEFINITELY_FAKE": "red"}[verdict]