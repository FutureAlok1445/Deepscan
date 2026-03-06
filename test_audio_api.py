import requests
import json

url = "http://localhost:8000/api/v1/analyze"
files = {"file": ("test_synthetic.wav", open("test_synthetic.wav", "rb"), "audio/wav")}
data = {"language": "en"}

print("Uploading test_synthetic.wav...")
try:
    resp = requests.post(url, files=files, data=data, timeout=120)
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        result = resp.json()
        ts = result.get("trustScore", result.get("trust_score", "N/A"))
        verdict = result.get("verdict", "N/A")
        print(f"Trust Score: {ts}")
        print(f"Verdict: {verdict}")
        
        sub = result.get("subScores", result.get("sub_scores", {}))
        print(f"Sub-Scores: {json.dumps(sub, indent=2)}")
        
        findings = result.get("keyFindings", result.get("findings", []))
        print(f"Key Findings ({len(findings)}):")
        for f in findings[:10]:
            eng = f.get("engine", "?")
            score = f.get("score", "?")
            detail = f.get("detail", "")[:120]
            print(f"  - [{eng}] score={score} -- {detail}")
        
        # Also check CDCF data
        cdcf = result.get("cdcf", {})
        if cdcf:
            print(f"\nCDCF aacs={cdcf.get('aacs')} verdict={cdcf.get('verdict')}")
            print(f"CDCF sub_scores={cdcf.get('sub_scores')}")
            print(f"CDCF contradictions={cdcf.get('contradictions')}")
    else:
        print(resp.text[:500])
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
