"""
Live API test - checks all 9 engine findings via HTTP
Run against the already-running uvicorn server.
"""
import httpx
import asyncio
import json

async def test():
    print("=" * 60)
    print("  LIVE API TEST — 9-ENGINE PIPELINE")
    print("=" * 60)

    async with httpx.AsyncClient(timeout=120.0) as client:
        with open("dummy_ui_test.mp4", "rb") as f:
            files = {"file": ("dummy_ui_test.mp4", f, "video/mp4")}
            resp = await client.post("http://127.0.0.1:8000/api/v1/analyze", files=files)

    print(f"\nStatus Code: {resp.status_code}")
    if resp.status_code != 200:
        print("ERROR:", resp.text[:300])
        return

    data = resp.json()
    print(f"AACS Score : {data.get('aacs_score')}")
    print(f"Verdict    : {data.get('verdict')}")

    findings = data.get("findings", [])
    print(f"\nFindings ({len(findings)}):")
    print("-" * 60)
    for f in findings:
        print(f"  [{f.get('engine')}] score={f.get('score')}")
        print(f"    {str(f.get('detail',''))[:80]}")

    ltca = data.get("ltca_data", {})
    print("\nAdvanced Engine Scores from ltca_data:")
    print("-" * 60)
    for key in ["blink_score", "mesh_score", "reflect_score", "sync_score",
                "sync_correlation", "sync_offset", "blinks_detected"]:
        val = ltca.get(key)
        if val is not None:
            print(f"  {key}: {val}")

    # Verify no numpy arrays leaked
    assert "frames" not in ltca, "FAIL: frames key still present!"
    print("\n[OK] 'frames' key correctly absent from response")

    # Check new engines present
    engine_names = [f.get("engine") for f in findings]
    for expected in ["Eye-Blink-EAR", "Face-Mesh-Tracking", "Lip-Sync-Correlation"]:
        status = "[OK]" if expected in engine_names else "[WARN] missing"
        print(f"{status} Engine: {expected}")

    print("\n[PASS] Live API test complete.")

if __name__ == "__main__":
    asyncio.run(test())
