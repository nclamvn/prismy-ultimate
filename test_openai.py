import os
from openai import OpenAI

# Get API key from environment
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key[:20]}..." if api_key else "No API key found")

try:
    # Initialize client
    client = OpenAI(api_key=api_key)
    
    # Test translation
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a translator. Translate to Vietnamese."},
            {"role": "user", "content": "Hello World! How are you today?"}
        ],
        temperature=0.3,
        max_tokens=100
    )
    
    print(f"Translation: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"Error: {e}")
