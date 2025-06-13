import re

with open('src/api/v1/large_document.py', 'r') as f:
    content = f.read()

# Thêm import
if 'from src.celery_tasks.prismy_tasks import extract_text' not in content:
    import_pos = content.find('from pathlib import Path')
    content = content[:import_pos] + 'from src.celery_tasks.prismy_tasks import extract_text\n' + content[import_pos:]

# Thêm task call sau r.hset
pattern = r'(r\.hset\(job_key, mapping=job_data\))'
replacement = r'\1\n    \n    # Queue extraction task\n    task = extract_text.apply_async(args=[job_id, str(temp_path)], queue="extraction")\n    logger.info(f"Queued extraction task {task.id} for job {job_id}")'

content = re.sub(pattern, replacement, content)

with open('src/api/v1/large_document.py', 'w') as f:
    f.write(content)

print("Fixed!")
