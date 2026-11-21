import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Read the API keys from .env
keys_string = os.getenv("LLM_API_KEYS", "")

keys = [
    key.strip()
    for key in keys_string.split(",")
    if key.strip()
]

# Read the model name from .env
model = os.getenv("LLM_MODEL", "")

# Remove LiteLLM provider prefix
model_name = model.replace("gemini/", "", 1)

if not keys:
    print("ERROR: No API keys found in .env")
    exit()

print(f"Testing model: {model_name}")
print(f"Number of keys found: {len(keys)}")

url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent"

for index, key in enumerate(keys, start=1):

    print(f"\nTesting key {index}...")

    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": key,
    }

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": "Say hello in one sentence."
                    }
                ]
            }
        ]
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        print("HTTP Status:", response.status_code)

        if response.ok:
            data = response.json()

            text = (
                data.get("candidates", [{}])[0]
                .get("content", {})
                .get("parts", [{}])[0]
                .get("text", "")
            )

            print("SUCCESS!")
            print("Response:", text)

        else:
            print("API Error:", response.text[:1000])

    except requests.exceptions.RequestException as e:
        print("Request failed:", str(e))