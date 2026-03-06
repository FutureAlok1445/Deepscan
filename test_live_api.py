import httpx
import asyncio
import json

async def test_api():
    print("Sending video to live API...")
    async with httpx.AsyncClient() as client:
        with open("dummy_ui_test.mp4", "rb") as f:
            files = {"file": ("dummy_ui_test.mp4", f, "video/mp4")}
            response = await client.post("http://127.0.0.1:8000/api/v1/analyze", files=files, timeout=60.0)
            
            print(f"Status Code: {response.status_code}")
            data = response.json()
            print("Response Keys:", list(data.keys()))
            ltca = data.get("ltca_data", {})
            print("LTCA Keys:", list(ltca.keys()))
            if "nlm_report" in ltca:
                print("NLM Report Found! snippet:", ltca["nlm_report"][:100])
            else:
                print("NLM_REPORT IS MISSING FROM HTTP RESPONSE")

if __name__ == "__main__":
    asyncio.run(test_api())
