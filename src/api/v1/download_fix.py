# download_fix.py - Priority check result first
import json
import os
import redis
import logging
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, RedirectResponse
from src.storage.storage_manager import get_storage_manager

logger = logging.getLogger(__name__)

def create_fixed_download_endpoint(router: APIRouter):
    """Create fixed download endpoint - check result first"""
    
    @router.get("/download/{job_id}")
    async def download_result(job_id: str):
        """Download result - check S3/storage first, then local"""
        r = redis.from_url("redis://localhost:6379")
        
        # First check if we have the result stored
        result_key = f"result:{job_id}"
        result = r.get(result_key)
        
        if result:
            # We have the result, get storage info
            job_data = r.hgetall(f"prismy:job:{job_id}")
            
            # Check for storage info
            storage_info_str = job_data.get(b'storage_info', b'').decode('utf-8')
            
            if storage_info_str:
                # File stored in S3/storage system
                try:
                    storage_info = json.loads(storage_info_str)
                    storage_manager = get_storage_manager()
                    
                    # Get download URL
                    original_filename = job_data.get(b'file_path', b'output.pdf').decode('utf-8')
                    filename = f"translated_{Path(original_filename).name}"
                    
                    download_url = storage_manager.get_download_url(
                        storage_info,
                        filename=filename,
                        expiration=3600
                    )
                    
                    if storage_info.get('storage_type') == 's3':
                        # Redirect to S3 URL
                        return RedirectResponse(url=download_url)
                    else:
                        # Serve local file
                        file_path = storage_info.get('absolute_path', storage_info.get('path'))
                        if os.path.exists(file_path):
                            return FileResponse(
                                path=file_path,
                                filename=filename,
                                media_type='application/pdf'
                            )
                        
                except Exception as e:
                    logger.error(f"Error retrieving file from storage: {e}")
            
            # Fallback to result data
            result_data = json.loads(result)
            output_path = result_data.get("output_path")
            
            if output_path and os.path.exists(output_path):
                # Get original filename for better download name
                original_filename = job_data.get(b'file_path', b'output.pdf').decode('utf-8')
                filename = f"translated_{Path(original_filename).name}"
                
                return FileResponse(
                    path=output_path,
                    filename=filename,
                    media_type='application/pdf'
                )
        
        # Fallback to job data
        job_data = r.hgetall(f"prismy:job:{job_id}")
        if not job_data:
            raise HTTPException(status_code=404, detail="Job not found")
        
        status = job_data.get(b'status', b'').decode('utf-8')
        if status != 'completed':
            raise HTTPException(
                status_code=400,
                detail=f"Job not completed. Current status: {status}"
            )
        
        output_path = job_data.get(b'output_path', b'').decode('utf-8')
        if not output_path or not os.path.exists(output_path):
            raise HTTPException(status_code=404, detail="Output file not found")
        
        # Get original filename
        original_filename = job_data.get(b'file_path', b'output.pdf').decode('utf-8')
        filename = f"translated_{Path(original_filename).name}"
        
        return FileResponse(
            path=output_path,
            filename=filename,
            media_type='application/pdf'
        )
    
    return router
