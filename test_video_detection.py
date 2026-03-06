"""
Run all 3 test videos through the DetectionOrchestrator and compare scores.
Expected: real_video < 35, ai_video > 60, slight_ai = 35-60
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from backend.services.detection.orchestrator import DetectionOrchestrator

async def main():
    orch = DetectionOrchestrator()
    await orch.load_models()
    print()

    tests = [
        ("test_videos/real_video.mp4", "video/mp4", "REAL VIDEO", "< 35 (AUTHENTIC)"),
        ("test_videos/ai_video.mp4", "video/mp4", "AI-GENERATED VIDEO", "> 60 (DEEPFAKE)"),
        ("test_videos/slight_ai.mp4", "video/mp4", "SLIGHTLY-AI VIDEO", "35–60 (UNCERTAIN)"),
    ]

    results = []
    for path, mime, label, expected in tests:
        print(f"=== {label} ===")
        result = await orch.process_media(path, mime)
        score = result.get('aacs_score') or result.get('score', 0)
        verdict = result.get('verdict', 'N/A')
        mas = result.get('sub_scores', {}).get('mas', 'N/A')
        nlm = result.get('ltca_data', {}).get('nlm_report', 'N/A')

        results.append((label, score, verdict, expected))
        print(f"  AACS Score : {score}")
        print(f"  MAS Score  : {mas}")
        print(f"  Verdict    : {verdict}")
        print(f"  Expected   : {expected}")
        ok = "✅ PASS" if (
            (label == "REAL VIDEO" and score < 35) or
            (label == "AI-GENERATED VIDEO" and score > 60) or
            (label == "SLIGHTLY-AI VIDEO" and 35 <= score <= 60)
        ) else "❌ FAIL"
        print(f"  Result     : {ok}")
        print(f"  NLM snippet: {str(nlm)[:80]}...")
        print()

    print("=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for label, score, verdict, expected in results:
        ok = "✅" if (
            (label == "REAL VIDEO" and score < 35) or
            (label == "AI-GENERATED VIDEO" and score > 60) or
            (label == "SLIGHTLY-AI VIDEO" and 35 <= score <= 60)
        ) else "❌"
        print(f"  {ok} {label}: {score:.1f} ({verdict}) — expected {expected}")

if __name__ == "__main__":
    asyncio.run(main())
