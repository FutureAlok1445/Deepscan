import httpx
from bs4 import BeautifulSoup
class UrlScraper:
    async def extract_media(self, url: str) -> list:
        try:
            async with httpx.AsyncClient() as client:
                soup = BeautifulSoup((await client.get(url, timeout=10.0)).text, 'html.parser')
                return [img.get('src') for img in soup.find_all('img') if img.get('src')]
        except Exception: return []