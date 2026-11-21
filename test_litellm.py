import os
from dotenv import load_dotenv
from litellm import completion

load_dotenv()

keys = [
    key.strip()
    for key in os.getenv("LLM_API_KEYS", "").split(",")
    if key.strip()
]

model = os.getenv("LLM_MODEL", "gemini/gemini-3.8-flash")

print("Model:", model)
print("Keys found:", len(keys))

if not keys:
    raise RuntimeError("No API keys found")

for i, key in enumerate(keys, start=1):

    print(f"\nTesting key {i}...")

    try:

        response = completion(
            model=model,
            messages=[
                {
                    "role": "user",
                    "content": "Say hello in one sentence."
                }
            ],
            api_key=key,
            timeout=120,
            max_retries=0,
        )

        print("SUCCESS")

        print(
            response.choices[0].message.content
        )

        break

    except Exception as e:

        print("FAILED")
        print(type(e).__name__)
        print(str(e))