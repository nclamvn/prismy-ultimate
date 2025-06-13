from celery import Celery
from kombu import Queue
import os
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

app = Celery(
    'prismy_ultimate',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'prismy_tasks.extract_text': {'queue': 'extraction'},
        'prismy_tasks.translate_chunks': {'queue': 'translation'},
        'prismy_tasks.reconstruct_document': {'queue': 'reconstruction'},
        'prismy_tasks.process_translation': {'queue': 'default'},
    },
    task_default_queue='default',
    task_queues=(
        Queue('celery'),
        Queue('default'),
        Queue('extraction'),
        Queue('translation'),
        Queue('reconstruction'),
    ),
)

# Auto-discover tasks
app.autodiscover_tasks(['src.celery_tasks'])
try:
    import src.celery_tasks.prismy_tasks
    print("✓ Imported prismy_tasks successfully")
except Exception as e:
    print(f"✗ Failed to import prismy_tasks: {e}")