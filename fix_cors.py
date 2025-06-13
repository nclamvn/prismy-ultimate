import re

# Read main.py
with open('src/api/main.py', 'r') as f:
    content = f.read()

# Check if CORS already configured
if 'CORSMiddleware' not in content:
    # Add CORS import
    if 'from fastapi.middleware.cors import CORSMiddleware' not in content:
        content = re.sub(
            r'(from fastapi import [^\n]+)',
            r'\1\nfrom fastapi.middleware.cors import CORSMiddleware',
            content
        )
    
    # Add CORS middleware after app creation
    app_pattern = r'(app = FastAPI\([^)]*\))'
    cors_config = '''

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)'''
    
    content = re.sub(app_pattern, r'\1' + cors_config, content)
    
    with open('src/api/main.py', 'w') as f:
        f.write(content)
    
    print("✅ CORS configured")
else:
    print("ℹ️  CORS already configured")
