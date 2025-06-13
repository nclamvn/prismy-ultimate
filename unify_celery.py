with open('src/celery_tasks/prismy_tasks.py', 'r') as f:
    content = f.read()

# Replace celery_app with app from main celery_app
content = content.replace('from celery import Celery', 'from celery_app import app as celery_app')
content = content.replace('''celery_app = Celery(
    'prismy_tasks',
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL
)''', '# Use main celery app')

with open('src/celery_tasks/prismy_tasks.py', 'w') as f:
    f.write(content)

print("Unified celery app!")
