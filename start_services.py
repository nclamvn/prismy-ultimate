import subprocess
import time
import os
import sys

def start_services():
    print("🚀 Starting PRISMY Ultimate Services...")
    
    os.environ['PYTHONPATH'] = os.getcwd()
    
    print("\n1️⃣ Checking Redis...")
    try:
        subprocess.run(['redis-cli', 'ping'], check=True, capture_output=True)
        print("✅ Redis is running")
    except:
        print("Starting Redis...")
        subprocess.Popen(['redis-server', '--daemonize', 'yes'])
        time.sleep(2)
    
    print("\n2️⃣ Starting Celery Worker...")
    celery_worker = subprocess.Popen([
        sys.executable, '-m', 'celery', '-A', 'celery_app', 'worker',
        '--loglevel=info',
        '--pool=solo',
        '-Q', 'extraction,translation,reconstruction'
    ])
    print(f"✅ Celery Worker PID: {celery_worker.pid}")
    
    time.sleep(3)
    
    print("\n3️⃣ Starting Flower...")
    flower = subprocess.Popen([
        sys.executable, '-m', 'celery', '-A', 'celery_app', 'flower',
        '--port=5555'
    ])
    print(f"✅ Flower PID: {flower.pid}")
    
    time.sleep(2)
    
    print("\n4️⃣ Starting FastAPI...")
    api = subprocess.Popen([
        sys.executable, '-m', 'uvicorn', 'src.api.main:app',
        '--reload', '--host', '0.0.0.0', '--port', '8000'
    ])
    print(f"✅ FastAPI PID: {api.pid}")
    
    with open('.pids', 'w') as f:
        f.write(f"{celery_worker.pid}\n")
        f.write(f"{flower.pid}\n") 
        f.write(f"{api.pid}\n")
    
    print("""
✅ All services started!

📍 Access points:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Flower: http://localhost:5555

To stop: python stop_services.py
""")
    
    try:
        api.wait()
    except KeyboardInterrupt:
        print("\n⏹️ Stopping services...")
        celery_worker.terminate()
        flower.terminate()
        api.terminate()

if __name__ == "__main__":
    start_services()