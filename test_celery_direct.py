import os
os.environ['PYTHONPATH'] = '/Users/mac/prismy-ultimate'

from celery import Celery

app = Celery('test', 
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

@app.task
def simple_test(x, y):
    return x + y

if __name__ == '__main__':
    # Start worker in background
    import subprocess
    worker = subprocess.Popen([
        'celery', '-A', 'test_celery_direct', 'worker', '--loglevel=info'
    ])
    
    import time
    time.sleep(3)  # Wait for worker to start
    
    result = simple_test.delay(4, 4)
    print(f"Task ID: {result.id}")
    print(f"Result: {result.get(timeout=5)}")
    
    worker.terminate()
