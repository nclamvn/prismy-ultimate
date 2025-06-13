with open('src/services/queue/manager.py', 'r') as f:
    content = f.read()

# Change task name to match what worker sees
content = content.replace(
    "app.send_task('prismy_tasks.extract_text'",
    "app.send_task('src.celery_tasks.prismy_tasks.extract_text'"
)

# Also fix the import
content = content.replace(
    "from src.celery_tasks.prismy_tasks import extract_text",
    "# Use send_task instead of importing to avoid circular import"
)

# Fix the apply_async call
old_call = "task = extract_text.apply_async(args=[job_id, file_path, \"pdf\"])"
new_call = """task = app.send_task('src.celery_tasks.prismy_tasks.extract_text', 
                                 args=[job_id, file_path, \"pdf\"],
                                 queue='extraction')"""

content = content.replace(old_call, new_call)

# Add app import if needed
if "from celery import current_app" not in content:
    import_section = content.split('\n\n')[0]
    content = content.replace(import_section, import_section + '\nfrom celery import current_app as app')

with open('src/services/queue/manager.py', 'w') as f:
    f.write(content)

print("Fixed task names!")
