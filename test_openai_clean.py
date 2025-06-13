import os
import httpx

# Clear any proxy settings
os.environ.pop('HTTP_PROXY', None)
os.environ.pop('HTTPS_PROXY', None)
os.environ.pop('http_proxy', None)
os.environ.pop('https_proxy', None)

from openai import OpenAI

# Get API key from environment
api_key = os.getenv('OPENAI_API_KEY')
print(f"API Key: {api_key[:20]}..." if api_key else "No API key found")

try:
    # Initialize client without proxy
    client = OpenAI(
        api_key=api_key,
        http_client=httpx.Client(proxy=None)
    )
    
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
