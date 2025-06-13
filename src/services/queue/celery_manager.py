import redis
import json
import uuid
from typing import Dict, Any, Optional

def get_celery_tasks():
    from src.celery_tasks.prismy_tasks import extract_text, process_translation
    return extract_text, process_translation

from datetime import datetime

class CeleryQueueManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
    def create_job(self, job_data: Dict[str, Any]) -> str:
        job_id = str(uuid.uuid4())
        job_info = {
            'id': job_id,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'data': job_data,
            'progress': 0,
            'stage': 'queued'
        }
        self.redis_client.setex(
            f"job:{job_id}",
            3600,
            json.dumps(job_info)
        )
        return job_id
    
    def submit_extraction(self, job_data: Dict[str, Any]) -> str:
        job_id = self.create_job(job_data)
        
        extract_task, _ = get_celery_tasks()
        extract_task.apply_async(
            args=[job_id, job_data['file_path'], job_data['file_type']],
            queue='extraction',
            task_id=f"extract_{job_id}"
        )
        
        self.update_job_status(job_id, 'processing', {'stage': 'extraction'})
        return job_id
    
    def submit_pdf_translation(self, file_path: str, target_language: str, tier: str = 'basic') -> str:
        _, process_task = get_celery_tasks()
        job_id = str(uuid.uuid4())
        
        job_info = {
            'id': job_id,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'file_path': file_path,
            'target_language': target_language,
            'tier': tier,
            'progress': 0,
            'stage': 'queued'
        }
        self.redis_client.setex(
            f"job:{job_id}",
            3600,
            json.dumps(job_info)
        )
        
        result = process_task.apply_async(
            args=[job_id, file_path, 'pdf', target_language, tier],
            queue='extraction'
        )
        
        self.update_job_status(job_id, 'processing', {'stage': 'extraction'})
        return job_id
    
    def submit_text_translation(self, text: str, target_language: str, tier: str = 'basic') -> str:
        _, process_task = get_celery_tasks()
        job_id = str(uuid.uuid4())
        
        # Save text to temp file
        import tempfile
        import os
        temp_dir = "storage/temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.txt',
            dir=temp_dir,
            delete=False
        ) as f:
            f.write(text)
            file_path = f.name
        
        job_info = {
            'id': job_id,
            'status': 'pending',
            'created_at': datetime.utcnow().isoformat(),
            'file_path': file_path,
            'target_language': target_language,
            'tier': tier,
            'progress': 0,
            'stage': 'queued'
        }
        self.redis_client.setex(
            f"job:{job_id}",
            3600,
            json.dumps(job_info)
        )
        
        result = process_task.apply_async(
            args=[job_id, file_path, 'text', target_language, tier],
            queue='extraction'
        )
        
        self.update_job_status(job_id, 'processing', {'stage': 'extraction'})
        return job_id
    
    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        job_data = self.redis_client.get(f"job:{job_id}")
        if job_data:
            return json.loads(job_data)
        return None
    
    def update_job_status(self, job_id: str, status: str, data: Optional[Dict[str, Any]] = None):
        job_info = self.get_job_status(job_id)
        if job_info:
            job_info['status'] = status
            job_info['updated_at'] = datetime.utcnow().isoformat()
            
            if data:
                if 'progress' in data:
                    job_info['progress'] = data['progress']
                if 'stage' in data:
                    job_info['stage'] = data['stage']
                if 'result' in data:
                    job_info['result'] = data['result']
                if 'error' in data:
                    job_info['error'] = data['error']
                if 'output_file' in data:
                    job_info['output_file'] = data['output_file']
                if 'download_url' in data:
                    job_info['download_url'] = data['download_url']
            
            self.redis_client.setex(
                f"job:{job_id}",
                3600,
                json.dumps(job_info)
            )
    
    def list_jobs(self, status: Optional[str] = None) -> list:
        jobs = []
        for key in self.redis_client.scan_iter("job:*"):
            job_data = self.redis_client.get(key)
            if job_data:
                job = json.loads(job_data)
                if status is None or job.get('status') == status:
                    jobs.append(job)
        return sorted(jobs, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def cleanup_old_jobs(self, hours: int = 24):
        from datetime import timedelta
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        for key in self.redis_client.scan_iter("job:*"):
            job_data = self.redis_client.get(key)
            if job_data:
                job = json.loads(job_data)
                created_at = datetime.fromisoformat(job.get('created_at', ''))
                if created_at < cutoff_time:
                    self.redis_client.delete(key)