with open('src/services/queue/manager.py', 'r') as f:
    content = f.read()

# Fix the extract_text call to include file_type
old_line = 'task = extract_text.apply_async(args=[job_id, file_path], queue="extraction")'
new_line = 'task = extract_text.apply_async(args=[job_id, file_path, "pdf"], queue="extraction")'

content = content.replace(old_line, new_line)

with open('src/services/queue/manager.py', 'w') as f:
    f.write(content)

print("Fixed extract_text arguments!")
