from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import os
import aiofiles
from src.services.queue.celery_manager import CeleryQueueManager

router = APIRouter()
queue_manager = CeleryQueueManager()

@router.post("/translate/pdf/async")
async def translate_pdf_async(
    file: UploadFile = File(...),
    target_language: str = Form(...),
    tier: str = Form("basic")
):
    try:
        temp_dir = "storage/temp"
        os.makedirs(temp_dir, exist_ok=True)
        
        file_path = os.path.join(temp_dir, file.filename)
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)
        
        job_id = queue_manager.submit_pdf_translation(
            file_path=file_path,
            target_language=target_language,
            tier=tier
        )
        
        return JSONResponse({
            "job_id": job_id,
            "status": "processing",
            "message": "Translation job submitted successfully"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/translate/job/{job_id}")
async def get_job_status(job_id: str):
    job_info = queue_manager.get_job_status(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JSONResponse(job_info)

@router.get("/translate/job/{job_id}/download")
async def download_result(job_id: str):
    job_info = queue_manager.get_job_status(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    if job_info.get('status') != 'completed':
        raise HTTPException(
            status_code=400, 
            detail=f"Job is {job_info.get('status')}, not completed"
        )
    
    output_file = job_info.get("output_path")
    if not output_file or not os.path.exists(output_file):
        raise HTTPException(status_code=404, detail="Output file not found")
    
    return FileResponse(
        output_file,
        media_type='application/pdf',
        filename=os.path.basename(output_file)
    )

@router.get("/translate/jobs")
async def list_jobs(status: Optional[str] = None):
    jobs = queue_manager.list_jobs(status)
    return JSONResponse({
        "total": len(jobs),
        "jobs": jobs
    })

@router.post("/translate/text/async")
async def translate_text_async(
    text: str = Form(...),
    target_language: str = Form(...),
    tier: str = Form("basic")
):
    try:
        job_id = queue_manager.submit_text_translation(
            text=text,
            target_language=target_language,
            tier=tier
        )
        
        return JSONResponse({
            "job_id": job_id,
            "status": "processing",
            "message": "Translation job submitted successfully"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/translate/job/{job_id}")
async def cancel_job(job_id: str):
    job_info = queue_manager.get_job_status(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="Job not found")
    
    queue_manager.update_job_status(job_id, 'cancelled')
    
    return JSONResponse({
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job cancelled successfully"
    })

@router.get("/outputs")
async def list_outputs():
    """List all output files"""
    import os
    from pathlib import Path
    
    output_dir = Path("outputs")
    if not output_dir.exists():
        return {"files": []}
    
    files = []
    for file in output_dir.glob("translated_*.txt"):
        files.append({
            "filename": file.name,
            "size": file.stat().st_size,
            "job_id": file.stem.replace("translated_", "")
        })
    
    return {"files": files}


@router.get("/outputs/{filename}/download")
async def download_output_direct(filename: str):
    """Download output file directly by filename"""
    from pathlib import Path
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    
    file_path = Path("outputs") / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )


@router.get("/outputs")
async def list_outputs():
    """List all output files"""
    import os
    from pathlib import Path
    
    output_dir = Path("outputs")
    if not output_dir.exists():
        return {"files": []}
    
    files = []
    for file in output_dir.glob("translated_*.txt"):
        files.append({
            "filename": file.name,
            "size": file.stat().st_size,
            "job_id": file.stem.replace("translated_", "")
        })
    
    return {"files": files}


@router.get("/outputs/{filename}/download")
async def download_output_direct(filename: str):
    """Download output file directly by filename"""
    from pathlib import Path
    from fastapi.responses import FileResponse
    from fastapi import HTTPException
    
    file_path = Path("outputs") / filename
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="File not found")
    
    return FileResponse(
        path=str(file_path),
        filename=filename,
        media_type='application/octet-stream'
    )
