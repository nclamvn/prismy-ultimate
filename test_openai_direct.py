import os
from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
print(f"Testing OpenAI with key: {api_key[:20]}...")

try:
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Translate to Vietnamese"},
            {"role": "user", "content": "Hello World"}
        ],
        max_tokens=50
    )
    print(f"Success! Translation: {response.choices[0].message.content}")
except Exception as e:
    print(f"Error: {e}")
