import re

with open('src/celery_tasks/prismy_tasks.py', 'r') as f:
    content = f.read()

# Add @celery_app.task before each function
functions = [
    ('def extract_text(', '@celery_app.task(name="prismy_tasks.extract_text")\ndef extract_text('),
    ('def translate_chunks(', '@celery_app.task(name="prismy_tasks.translate_chunks")\ndef translate_chunks('),
    ('def reconstruct_document(', '@celery_app.task(name="prismy_tasks.reconstruct_document")\ndef reconstruct_document(')
]

for old, new in functions:
    content = content.replace(old, new)

with open('src/celery_tasks/prismy_tasks.py', 'w') as f:
    f.write(content)

print("Added task decorators!")
