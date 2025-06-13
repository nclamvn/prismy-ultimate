import re

with open('src/api/celery_endpoints.py', 'r') as f:
    content = f.read()

# Find and fix the download endpoint
pattern = r'output_file = job_info\.get\(["\']output_file["\']\)'
replacement = 'output_file = job_info.get("output_path")'

content = re.sub(pattern, replacement, content)

# Also check if there's a Path check that needs fixing
if 'Path(output_file)' in content and 'output_path' not in content:
    content = content.replace('if not Path(output_file).exists():', 'if not output_file or not Path(output_file).exists():')

with open('src/api/celery_endpoints.py', 'w') as f:
    f.write(content)

print("Fixed download path checking")
