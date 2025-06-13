import os
import sys
import subprocess
import pathlib
import time
import signal

ROOT = pathlib.Path(__file__).resolve().parent
os.environ['PYTHONPATH'] = str(ROOT)

def main():
    print("🚀 Starting PRISMY Ultimate services...")
    
    processes = []
    
    try:
        api_process = subprocess.Popen(
            [sys.executable, '-m', 'uvicorn', 'src.api.main:app', '--host', '0.0.0.0', '--port', '8000'],
            cwd=ROOT
        )
        processes.append(api_process)
        print("✅ API server started on port 8000")
        
        time.sleep(2)
        
        worker_process = subprocess.Popen(
            [sys.executable, '-m', 'celery', '-A', 'celery_app', 'worker', 
             '--pool=solo', '--concurrency=1',
             '-Q', 'celery,default,extraction,translation,reconstruction',
             '--loglevel=INFO'],
            cwd=ROOT
        )
        processes.append(worker_process)
        print("✅ Celery worker started")
        
        redis_process = subprocess.Popen(['redis-server'])
        processes.append(redis_process)
        print("✅ Redis server started")
        
        print("\n✅ All services started successfully!")
        print("📡 API: http://localhost:8000")
        print("📡 Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop all services...")
        
        for p in processes:
            p.wait()
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping all services...")
        for p in processes:
            p.terminate()
        for p in processes:
            p.wait()
        print("✅ All services stopped")

if __name__ == "__main__":
    main()