def format_result(result: dict) -> str:
    """Format an analysis result into a Telegram-friendly message."""
    score = result.get("aacs_score", result.get("score", 0))
    verdict = result.get("verdict", "UNKNOWN")
    sub = result.get("sub_scores", {})
    fusion = result.get("fusion", {})
    elapsed = result.get("elapsed_seconds", 0)

    # Verdict emoji
    emoji_map = {
        "AUTHENTIC": "✅",
        "UNCERTAIN": "⚠️",
        "LIKELY_FAKE": "🟠",
        "DEFINITELY_FAKE": "🔴",
    }
    emoji = emoji_map.get(verdict, "❓")

    # Build the response
    lines = [
        f"🔍 *DeepScan Analysis Complete*",
        f"",
        f"{emoji} *Verdict: {verdict.replace('_', ' ')}*",
        f"📊 *AACS Score: {score:.1f}/100*",
        f"",
        f"📋 *Sub-Scores:*",
        f"  • MAS (Media): `{sub.get('mas', 0):.1f}`",
        f"  • PPS (Physiological): `{sub.get('pps', 0):.1f}`",
        f"  • IRS (Information): `{sub.get('irs', 0):.1f}`",
        f"  • AAS (Acoustic): `{sub.get('aas', 0):.1f}`",
        f"  • CVS (Context): `{sub.get('cvs', 0):.1f}`",
    ]

    # Contradictions
    contradictions = fusion.get("contradictions", [])
    if contradictions:
        lines.append(f"")
        lines.append(f"⚡ *CDCF: {len(contradictions)} contradiction(s)*")
        lines.append(f"  Multiplier: {fusion.get('multiplier', 1.0):.2f}x")

    # Narrative summary
    narrative = result.get("narrative", {})
    summary = narrative.get("summary", "")
    if summary and len(summary) > 10:
        lines.append(f"")
        lines.append(f"💬 _{summary[:200]}_")

    lines.append(f"")
    lines.append(f"⏱️ Analysis time: {elapsed}s")
    lines.append(f"_Powered by DeepScan AACS • Team Bug Bytes_")

    return "\n".join(lines)