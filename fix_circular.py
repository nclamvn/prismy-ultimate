with open('src/services/queue/manager.py', 'r') as f:
    content = f.read()

# Remove top-level import
content = content.replace('from src.celery_tasks.prismy_tasks import extract_text\n', '')

# Find the create_job method and add import inside
lines = content.split('\n')
new_lines = []
in_create_job = False

for i, line in enumerate(lines):
    new_lines.append(line)
    
    # Add import inside method after add_to_queue
    if 'await self.add_to_queue(self.EXTRACT_QUEUE, job_id)' in line:
        new_lines.append('')
        new_lines.append('        # Queue to Celery - import here to avoid circular dependency')
        new_lines.append('        from src.celery_tasks.prismy_tasks import extract_text')
        new_lines.append('        task = extract_text.apply_async(args=[job_id, file_path, "pdf"], queue="extraction")')
        new_lines.append('        logger.info(f"Queued Celery task {task.id} for job {job_id}")')

content = '\n'.join(new_lines)

# Remove any duplicate task calls
while '\n\n        # Also queue to Celery' in content:
    start = content.find('\n\n        # Also queue to Celery')
    end = content.find('\n', start + 200)
    content = content[:start] + content[end:]

with open('src/services/queue/manager.py', 'w') as f:
    f.write(content)

print("Fixed circular import!")
