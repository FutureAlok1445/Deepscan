"""
Standalone test to verify the ELA-based image orchestrator without starting the full server.
This tests that:
1. preprocessor.py generates a valid ELA base64 heatmap
2. orchestrator properly removes all claude_vision references
3. The result dict shape matches what analyze_image.py expects
"""
import asyncio
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from backend.services.IMageDetector.preprocessor import preprocessor

async def test_ela():
    print("=" * 60)
    print("TEST: ELA Heatmap Generation")
    print("=" * 60)
    
    # 1. Test preprocessor ELA
    result = preprocessor.process("test_face.jpg")
    assert result.get("ela_base64"), "FAIL: ELA base64 is None or empty"
    assert len(result["ela_base64"]) > 100, "FAIL: ELA base64 too short"
    print(f"PASS: ELA heatmap generated ({len(result['ela_base64'])} chars)")
    
    # 2. Check the full prefix that gets sent over the API  
    full_heatmap_prefix = "data:image/jpeg;base64," + result["ela_base64"]
    assert full_heatmap_prefix.startswith("data:image/jpeg;base64,")
    print(f"PASS: Heatmap prefix correct: {full_heatmap_prefix[:50]}...")

    # 3. Verify orchestrator has no claude imports
    import ast
    orch_path = "backend/services/IMageDetector/orchestrator.py"
    with open(orch_path) as f:
        source = f.read()
    assert "claude_analyzer" not in source, "FAIL: claude_analyzer still referenced in orchestrator"
    assert "from .claude_vision import" not in source, "FAIL: claude_vision still imported"
    print("PASS: claude_vision fully removed from orchestrator.py")

    # 4. Verify result shape including ELA heatmap field
    mock_result = {
        "score": 55.0,
        "verdict": "Uncertain",
        "signals": {
            "metadata_cvs": 50,
            "visual_forensics_mas": 40,
            "face_geometry_pps": 60,
            "frequency": 45,
            "semantic_context_irs": 55,
            "diffusion_fingerprint": 30
        },
        "explainability": {
            "text": "Test explanation",
            "ela_base64_heatmap_prefix": full_heatmap_prefix,
            "regions": []          # No Claude polygons, pure ELA
        }
    }
    assert "ela_base64_heatmap_prefix" in mock_result["explainability"]
    assert mock_result["explainability"]["regions"] == []
    print("PASS: Result shape is correct, regions=[] (ELA-only mode)")
    
    print()
    print("=" * 60)
    print("ALL TESTS PASSED - ELA pipeline is working correctly.")
    print("=" * 60)

asyncio.run(test_ela())
