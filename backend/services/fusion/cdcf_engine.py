"""
cdcf_engine.py — Cross-Detector Contradiction Fusion Engine

Detects contradictions between sub-scores (engines that disagree by >30 points)
and applies a penalty multiplier. Uses the bulletproof score_calculator.
"""
import math
from itertools import combinations
from backend.services.fusion.score_calculator import calculate_aacs, get_verdict, get_verdict_color


class CDCFEngine:
    def fuse(self, scores: dict, category: str = "unknown") -> dict:
        keys = ["mas", "pps", "irs", "aas", "cvs"]
        
        # Safely extract sub-scores, handling None/NaN
        sub_scores = {}
        for k in keys:
            val = scores.get(k, 0.0)
            try:
                val = float(val) if val is not None else 0.0
                if math.isnan(val) or math.isinf(val):
                    val = 0.0
            except (TypeError, ValueError):
                val = 0.0
            sub_scores[k] = val

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

        # calculate_aacs now returns a dict — extract the aacs float
        calc_result = calculate_aacs(**sub_scores, category=category)
        raw_aacs = calc_result["aacs"] if isinstance(calc_result, dict) else float(calc_result)
        
        final_aacs = min(100.0, max(0.0, raw_aacs * multiplier))
        vdct = get_verdict(final_aacs)
        
        note = (
            f"Multiple engines disagree ({len(contradictions)} contradictions). "
            f"Score scaled by {multiplier:.2f}x to penalize uncertainty."
            if contradictions else "All engines in agreement."
        )
        return {
            "aacs": round(float(final_aacs), 2),
            "verdict": vdct,
            "verdict_color": get_verdict_color(vdct),
            "contradictions": contradictions,
            "multiplier": round(multiplier, 4),
            "sub_scores": sub_scores,
            "confidence_note": note,
        }