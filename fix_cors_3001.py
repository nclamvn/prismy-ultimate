import re

with open('src/api/main.py', 'r') as f:
    content = f.read()

# Update CORS origins to include both ports
content = re.sub(
    r'allow_origins=\[".*?"\]',
    'allow_origins=["http://localhost:3000", "http://localhost:3001", "http://127.0.0.1:3000", "http://127.0.0.1:3001"]',
    content
)

with open('src/api/main.py', 'w') as f:
    f.write(content)

print("✅ CORS updated for port 3001")
