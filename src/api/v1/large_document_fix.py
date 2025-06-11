# Fix download endpoint - chỉ copy phần cần sửa
import json
from pathlib import Path
from fastapi import HTTPException
from fastapi.responses import FileResponse
import redis

# Replace the download endpoint
async def download_result_new(job_id: str):
    """Download translation result - Fixed to get from Redis result"""
    # Connect to Redis
    r = redis.from_url("redis://localhost:6379")
    
    # Check job exists
    job_data = r.hgetall(f"prismy:job:{job_id}")
    if not job_data:
        raise HTTPException(404, "Job not found")
    
    # Get result from Redis
    result_data = r.get(f"result:{job_id}")
    if not result_data:
        # Check status
        status = job_data.get(b'status', b'pending').decode('utf-8')
        raise HTTPException(400, f"Job not completed or result not found. Status: {status}")
    
    # Parse result
    try:
        result = json.loads(result_data)
        output_path = result.get('output_path')
        
        if not output_path:
            raise HTTPException(500, "Output path not found in result")
            
        if not Path(output_path).exists():
            raise HTTPException(404, f"Output file not found at: {output_path}")
        
        # Return the PDF file
        return FileResponse(
            output_path,
            filename=f"{job_id}_translated.pdf",
            media_type="application/pdf"
        )
        
    except json.JSONDecodeError:
        raise HTTPException(500, "Invalid result data")
    except Exception as e:
        raise HTTPException(500, f"Error retrieving file: {str(e)}")
