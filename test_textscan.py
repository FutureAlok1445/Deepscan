import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test Phishing 
        text_phishing = "URGENT: Verify your account immediately! Click here to update your password for paypal at http://bit.ly/fake-link."
        r1 = await client.post('http://localhost:8000/api/v1/analyze/text', json={'text': text_phishing, 'mode': 'phishing'})
        print(f"Phishing test status: {r1.status_code}")
        print(r1.json())
        
        # Test AI Detection
        text_ai = "In conclusion, the impact of artificial intelligence on modern society cannot be overstated. As an AI language model, I believe it is important to note that these advancements offer unprecedented opportunities."
        r2 = await client.post('http://localhost:8000/api/v1/analyze/text', json={'text': text_ai, 'mode': 'ai'})
        print(f"\nAI test status: {r2.status_code}")
        print(r2.json())

if __name__ == "__main__":
    asyncio.run(test_api())
