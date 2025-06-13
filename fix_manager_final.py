import re

with open('src/services/queue/manager.py', 'r') as f:
    content = f.read()

# Find the create_job method
pattern = r'(# Queue to Celery.*?\n.*?from.*?\n.*?task = .*?\n.*?logger\.info.*?\n)'

# Replace with proper send_task
replacement = '''        # Queue to Celery
        from celery import current_app as celery_app
        task = celery_app.send_task('prismy_tasks.extract_text', 
                                    args=[job_id, file_path, "pdf"],
                                    queue='extraction')
        logger.info(f"Queued Celery task {task.id} for job {job_id}")
'''

content = re.sub(pattern, replacement, content, flags=re.DOTALL)

with open('src/services/queue/manager.py', 'w') as f:
    f.write(content)

print("Fixed manager.py!")
