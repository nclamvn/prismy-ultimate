web: uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
worker: celery -A celery_app worker -n worker1@%h --pool=solo --concurrency=1 -Q celery,default,extraction,translation,reconstruction --loglevel=INFO
