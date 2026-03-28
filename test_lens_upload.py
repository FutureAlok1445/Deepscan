import requests
import re
from bs4 import BeautifulSoup

def google_lens_upload(image_path):
    print("Uploading to Google Lens directly...")
    url = "https://lens.google.com/upload"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    with open(image_path, 'rb') as f:
        files = {'encoded_image': (image_path, f, 'image/jpeg')}
        # A hack to pretend we are the browser: Lens needs `ep=ccm` or similar
        # let's try a simple multipart request
        try:
            r = requests.post(url, headers=headers, files=files, allow_redirects=True)
            print(f"Status: {r.status_code}")
            
            # Follow the generic matching strategy
            html = r.text
            matches = re.findall(r'\"([^\"]*? Wikipedia)\"', html)
            entities = set()
            for m in matches:
                entities.add(m)
            
            domains = set(re.findall(r'\"(https?://[^\"]+)\"', html))
            valid_domains = [d for d in domains if "google" not in d and "gstatic" not in d][:5]
            
            print(f"Entities: {entities}")
            print(f"Domains: {valid_domains}")
            return entities, valid_domains
        except Exception as e:
            print("Error:", e)

if __name__ == "__main__":
    import os
    if os.path.exists("test_face.jpg"):
        google_lens_upload("test_face.jpg")
    else:
        print("test_face.jpg not found")
