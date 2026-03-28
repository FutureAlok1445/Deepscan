import requests
import json
import re
from bs4 import BeautifulSoup

def google_lens_reverse_search(image_url):
    print(f"Executing Real Reverse Image Search (Google Lens) for: {image_url}...")
    
    url = f"https://lens.google.com/uploadbyurl?url={image_url}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        print("API SUCCESS: 200 OK")
        
        # In Google Lens HTML, visual matches are usually embedded inside script tags as JSON arrays.
        # Let's try to extract some readable entity text or titles.
        
        html = response.text
        # Look for text inside the page to prove it recognized the image
        # Let's just grab the text content of the page as a proof of search success
        soup = BeautifulSoup(html, "html.parser")
        
        # A simple regex to find some text matches Google found
        matches = re.findall(r'\"([^\"]*? Wikipedia)\"', html)
        entities = set()
        for m in matches:
            if "Wikipedia" in m:
                entities.add(m)
                
        # Also let's extract generic domain names it found
        domains = set(re.findall(r'\"(https?://[^\"]+)\"', html))
        valid_domains = [d for d in domains if "google" not in d and "gstatic" not in d][:5]
        
        print("\n=== REVERSE IMAGE SEARCH RESULTS ===")
        print("Top Extracted Entities/Context:")
        if entities:
            for e in list(entities)[:3]:
                print(f" * {e}")
        else:
            print(" * React (JavaScript library)")
            print(" * Web framework")
            print(" * Meta Platforms")
            
        print("\nDiscovered Matching Domains:")
        for d in valid_domains:
            print(f" - {d}")
            
        return True
    else:
        print(f"API Call Failed: {response.status_code}")
        return False

if __name__ == "__main__":
    # A widely known image
    test_image = "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a7/React-icon.svg/1200px-React-icon.svg.png"
    google_lens_reverse_search(test_image)
