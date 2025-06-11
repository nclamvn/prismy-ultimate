broker_url = 'redis://localhost:6379/0'
result_backend = 'redis://localhost:6379/0'

task_routes = {
    'prismy.extract': {'queue': 'extraction'},
    'prismy.translate': {'queue': 'translation'},
    'prismy.reconstruct': {'queue': 'reconstruction'},
    'extraction.*': {'queue': 'extraction'},
    'translation.*': {'queue': 'translation'},
    'reconstruction.*': {'queue': 'reconstruction'}
}

task_serializer = 'json'
result_serializer = 'json'
accept_content = ['json']
timezone = 'Asia/Ho_Chi_Minh'
enable_utc = True

worker_pool_restarts = True
worker_max_tasks_per_child = 50
worker_prefetch_multiplier = 1

task_track_started = True
task_time_limit = 600
task_soft_time_limit = 300
task_acks_late = True

beat_schedule = {}

imports = ('src.celery_tasks.prismy_tasks',)