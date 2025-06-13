import os
# Clear all proxy env vars
for key in list(os.environ.keys()):
    if 'proxy' in key.lower():
        del os.environ[key]

from openai import OpenAI

api_key = os.getenv('OPENAI_API_KEY')
print(f"Testing with key: {api_key[:30]}...")

try:
    client = OpenAI(api_key=api_key)
    
    # Simple test
    models = client.models.list()
    print(f"✓ Connected! Found {len(models.data)} models")
    
    # Translation test
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a translator. Translate to Vietnamese."},
            {"role": "user", "content": "Hello World! How are you today?"}
        ],
        max_tokens=100
    )
    
    print(f"✓ Translation: {response.choices[0].message.content}")
    
except Exception as e:
    print(f"✗ Error: {e}")
    print(f"Error type: {type(e).__name__}")
