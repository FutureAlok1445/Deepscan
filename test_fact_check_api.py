import asyncio
import httpx
from backend.config import settings

async def test_google_fact_check():
    query = "drinking bleach cures COVID-19"
    url = "https://factchecktools.googleapis.com/v1alpha1/claims:search"
    params = {"query": query, "languageCode": "en"}
    
    # Try with translate key if available
    if settings.GOOGLE_TRANSLATE_KEY:
        params["key"] = settings.GOOGLE_TRANSLATE_KEY
        
    print(f"Testing Google Fact Check API with query: {query}")
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, params=params)
        print(f"Status Code: {resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            claims = data.get("claims", [])
            print(f"Found {len(claims)} claims.")
            if claims:
                print(f"First Claim Rating: {claims[0].get('claimReview', [{}])[0].get('textualRating', 'N/A')}")
        else:
            print(f"Error Response: {resp.text}")

if __name__ == "__main__":
    asyncio.run(test_google_fact_check())
