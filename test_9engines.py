"""
Verification script: Test all 9 detection engines end-to-end.
Run from: c:\py project sem 4\Deepfake Main\Deepscan\
"""
import asyncio
import sys
sys.path.insert(0, '.')

async def run():
    from backend.services.detection.orchestrator import DetectionOrchestrator

    orch = DetectionOrchestrator()
    await orch.load_models()

    print("=" * 60)
    print("  9-ENGINE DETECTION PIPELINE TEST")
    print("=" * 60)

    result = await orch.process_media("dummy_ui_test.mp4", "video/mp4")

    print(f"\nAACS Score : {result['aacs_score']}")
    print(f"Verdict    : {result['verdict']}")
    print(f"\nFindings ({len(result['findings'])} total):")
    print("-" * 60)
    for f in result["findings"]:
        engine = f.get("engine", "?")
        score  = f.get("score", 0)
        detail = f.get("detail", "")[:70]
        print(f"  [{engine}]")
        print(f"    score={score}  {detail}")

    ltca = result.get("ltca_data", {})
    print("\nAdvanced Engine Details from ltca_data:")
    print("-" * 60)
    keys = [
        ("blink_score",   "blink_detail"),
        ("mesh_score",    "mesh_detail"),
        ("reflect_score", "reflect_detail"),
        ("sync_score",    "sync_detail"),
    ]
    for s_key, d_key in keys:
        score  = ltca.get(s_key, "N/A")
        detail = str(ltca.get(d_key, ""))[:70]
        print(f"  {s_key}: {score}")
        print(f"    detail: {detail}")

    sync_corr   = ltca.get("sync_correlation")
    sync_offset = ltca.get("sync_offset")
    blinks      = ltca.get("blinks_detected")
    print(f"\n  AV Correlation : {sync_corr}")
    print(f"  Frame Offset   : {sync_offset}")
    print(f"  Blinks Found   : {blinks}")

    vd = ltca.get("video_description", {})
    if vd:
        print("\nVideo Description:")
        print(f"  Setting: {vd.get('setting')}")
        print(f"  People : {vd.get('people')}")
        print(f"  Action : {vd.get('activity')}")
        print(f"  Moments: {len(vd.get('moments', []))} found")
    else:
        print("\n[WARN] No video_description found in ltca_data")

    # Check all frames key is NOT in response (serialization bug guard)
    assert "frames" not in ltca, "FAIL: 'frames' key still in ltca_data — serialization bug!"
    print("\n[OK] 'frames' key correctly stripped from ltca_data")
    print("[OK] Pipeline completed successfully")

if __name__ == "__main__":
    asyncio.run(run())
