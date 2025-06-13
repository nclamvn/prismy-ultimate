import sys
sys.path.append('/Users/mac/prismy-ultimate')

from src.celery_tasks.prismy_tasks import extract_text, translate_chunks, reconstruct_document
from celery import chain

# Test direct task
result = extract_text.delay('test-job-1', './test.pdf', 'pdf')
print(f"Extract task ID: {result.id}")
print(f"Extract task status: {result.status}")

# Wait a bit and check
import time
time.sleep(2)
print(f"After 2s - status: {result.status}")
