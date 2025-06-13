import os
import sys
print(f"Python: {sys.executable}")
print(f"OPENAI_API_KEY: {os.getenv('OPENAI_API_KEY', 'NOT SET')[:20]}...")

sys.path.insert(0, '/Users/mac/prismy-ultimate')
from src.services.translation_manager import translation_manager

print(f"Providers available: {list(translation_manager.providers.keys())}")
for name, provider in translation_manager.providers.items():
    print(f"  {name}: {provider.__class__.__name__}")
