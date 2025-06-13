# Check if endpoints exist in the right place
with open('src/api/celery_endpoints.py', 'r') as f:
    content = f.read()

# Check if router exists
if 'router = APIRouter' in content:
    print("Router found")
    # Check if outputs endpoint exists
    if '@router.get("/outputs")' in content:
        print("Outputs endpoint exists")
    else:
        print("Outputs endpoint NOT found - need to add it")
else:
    print("No router found - file structure issue")

# Show last 50 lines to debug
print("\nLast 50 lines of file:")
print("="*50)
lines = content.split('\n')
for line in lines[-50:]:
    print(line)
