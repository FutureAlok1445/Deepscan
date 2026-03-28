import requests
import json
import base64
import os

def groq_vision_api(image_path):
    print(f"Calling live Groq Vision API (llama-3.2-11b-vision-preview) on: {image_path}")
    
    # We must use the user's Groq key from config
    api_key = os.environ.get("GROQ_API_KEY", "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")
    
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        
    url = "https://api.groq.com/openai/v1/chat/completions"
        
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "llama-3.2-11b-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": "What does this image contain? Is there a face? Respond in 2 sentences."
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{encoded_string}"
                        }
                    }
                ]
            }
        ],
        "temperature": 1,
        "max_tokens": 1024,
        "top_p": 1,
        "stream": False,
        "stop": None
    }
    
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        print("API SUCCESS: 200 OK")
        result = response.json()
        print("\nGroq Vision Output Model Context:")
        print(result["choices"][0]["message"]["content"])
        return True
    else:
        print(f"API Failed: {response.status_code}")
        print(response.text)
        return False

if __name__ == "__main__":
    if os.path.exists("test_face.jpg"):
        groq_vision_api("test_face.jpg")
    else:
        print("test_face.jpg not found for vision analysis.")
