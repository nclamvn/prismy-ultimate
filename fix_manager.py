import re

with open('src/services/queue/manager.py', 'r') as f:
    content = f.read()

# Add import
if 'from src.celery_tasks.prismy_tasks import extract_text' not in content:
    imports = content.split('class QueueManager')[0]
    content = content.replace(imports, imports + 'from src.celery_tasks.prismy_tasks import extract_text\n\n')

# Fix add_to_queue to use Celery
old_pattern = r'await self\.add_to_queue\(self\.EXTRACT_QUEUE, job_id\)'
new_code = '''await self.add_to_queue(self.EXTRACT_QUEUE, job_id)
        
        # Also queue to Celery
        task = extract_text.apply_async(args=[job_id, file_path], queue="extraction")
        logger.info(f"Queued Celery task {task.id} for job {job_id}")'''

content = re.sub(old_pattern, new_code, content)

with open('src/services/queue/manager.py', 'w') as f:
    f.write(content)

print("Fixed QueueManager!")
