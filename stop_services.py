import subprocess
import os

def stop_services():
    print("🛑 Stopping PRISMY Ultimate services...")
    
    if os.path.exists('.pids'):
        with open('.pids', 'r') as f:
            pids = f.readlines()
            
        for pid in pids:
            try:
                pid = int(pid.strip())
                os.kill(pid, 15)
                print(f"Stopped process {pid}")
            except:
                pass
                
        os.remove('.pids')
    
    subprocess.run(['pkill', '-f', 'celery.*worker'], capture_output=True)
    subprocess.run(['pkill', '-f', 'celery.*flower'], capture_output=True)
    subprocess.run(['pkill', '-f', 'uvicorn.*main:app'], capture_output=True)
    
    print("✅ All services stopped!")

if __name__ == "__main__":
    stop_services()