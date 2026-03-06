from itertools import combinations
from backend.services.fusion.score_calculator import calculate_aacs, get_verdict, get_verdict_color

class CDCFEngine:
    def fuse(self, scores: dict, category: str = "unknown") -> dict:
        keys = ["mas", "pps", "irs", "aas", "cvs"]
        sub_scores = {k: float(scores.get(k, 0.0)) for k in keys}

        # Only check contradictions between applicable engines
        if category == "audio":
            applicable = ["mas", "aas"]
        elif category == "image":
            applicable = ["mas", "irs", "cvs"]
        elif category == "video":
            applicable = keys
        else:
            applicable = keys

        contradictions, multiplier = [], 1.0
        active_scores = [(k, sub_scores[k]) for k in applicable if sub_scores[k] > 0]
        for (k1, s1), (k2, s2) in combinations(active_scores, 2):
            if abs(s1 - s2) > 30.0:
                contradictions.append(f"{k1.upper()}↔{k2.upper()}")
                multiplier *= 1.03

        final_aacs = min(100.0, calculate_aacs(**sub_scores, category=category) * multiplier)
        vdct = get_verdict(final_aacs)
        
        note = f"Multiple engines disagree ({len(contradictions)} contradictions). Score scaled by {multiplier:.2f}x to penalize uncertainty." if contradictions else "All engines in agreement."
        return {
            "aacs": float(final_aacs), "verdict": vdct, "verdict_color": get_verdict_color(vdct),
            "contradictions": contradictions, "multiplier": multiplier, "sub_scores": sub_scores, "confidence_note": note
        }