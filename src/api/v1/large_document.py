"""
API endpoints for large document translation (500+ pages)
FIXED: Target language parameter handling and debug logs
"""
import json
from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks, Form
from fastapi.responses import JSONResponse, FileResponse
from typing import Optional
import os
import tempfile
from pathlib import Path
import logging
import uuid
from datetime import datetime

# Import Celery tasks directly
from src.celery_tasks.prismy_tasks import process_translation_sync
from src.core.models import JobStatus

logger = logging.getLogger(__name__)

router = APIRouter(tags=["large-documents"])

# ============================================
# HELPER FUNCTIONS FOR REDIS HASH OPERATIONS
# ============================================

def get_redis_client():
    """Get Redis client instance"""
    import redis
    return redis.from_url("redis://localhost:6379", decode_responses=True)

def store_job_data_as_hash(job_id: str, job_data: dict) -> None:
    """Store job data as Redis hash instead of string"""
    r = get_redis_client()
    
    # Convert job_data to hash-compatible format
    hash_data = {}
    for key, value in job_data.items():
        if isinstance(value, (dict, list)):
            hash_data[key] = json.dumps(value, ensure_ascii=False)
        else:
            hash_data[key] = str(value)
    
    # Add timestamps
    hash_data['created_at'] = datetime.utcnow().isoformat()
    hash_data['updated_at'] = datetime.utcnow().isoformat()
    
    # Store as hash with expiration
    r.hset(f"prismy:job:{job_id}", mapping=hash_data)
    r.expire(f"prismy:job:{job_id}", 86400)  # 24 hours expiration

def get_job_data_from_hash(job_id: str) -> dict:
    """Get job data from Redis hash"""
    r = get_redis_client()
    
    # Try hash first (new format)
    hash_data = r.hgetall(f"prismy:job:{job_id}")
    if hash_data:
        # Parse JSON fields back to objects
        for key in ['extraction_result', 'translation_result']:
            if key in hash_data and hash_data[key]:
                try:
                    hash_data[key] = json.loads(hash_data[key])
                except json.JSONDecodeError:
                    pass
        return hash_data
    
    # Fallback to old string format for backward compatibility
    job_data = r.get(f"prismy:job:{job_id}")
    if job_data:
        try:
            return json.loads(job_data)
        except json.JSONDecodeError:
            logger.error(f"Failed to parse job data for {job_id}")
            return {}
    
    return {}

def get_file_type_info(filename: str) -> dict:
    """Get file type information and detect correct file type"""
    file_extension = filename.lower().split('.')[-1] if '.' in filename else ''
    
    file_type_map = {
        'pdf': {
            'type': 'pdf',
            'description': 'PDF Document',
            'mime_types': ['application/pdf'],
            'celery_type': 'pdf'
        },
        'txt': {
            'type': 'text',
            'description': 'Text Document',
            'mime_types': ['text/plain'],
            'celery_type': 'txt'
        },
        'doc': {
            'type': 'word',
            'description': 'Word 97-2003 Document',
            'mime_types': ['application/msword'],
            'celery_type': 'docx'  # Use docx processor for both doc and docx
        },
        'docx': {
            'type': 'word',
            'description': 'Word 2007+ Document',
            'mime_types': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
            'celery_type': 'docx'
        }
    }
    
    return file_type_map.get(file_extension, {
        'type': 'unknown',
        'description': 'Unknown File Type',
        'mime_types': [],
        'celery_type': 'unknown'
    })

def estimate_processing_time(file_size_mb: float, file_type: str, total_pages: int = 1) -> dict:
    """Estimate processing time based on file type and size"""
    
    if file_type == 'pdf':
        # PDF: ~10-15 seconds per page
        minutes = max(2, int(total_pages * 0.2))
    elif file_type == 'word':
        # Word docs: ~5-10 seconds per estimated page
        minutes = max(2, int(total_pages * 0.1))
    else:
        # Text files: based on file size
        minutes = max(1, int(file_size_mb * 0.5))
    
    return {
        "minutes": minutes,
        "formatted": f"{minutes} minute{'s' if minutes != 1 else ''}"
    }

@router.post("/translate")
async def translate_large_document(
    file: UploadFile = File(...),
    source_lang: str = Form(default="auto"),  # ✅ FIXED: Use Form() with explicit default
    target_lang: str = Form(default="vi"),    # ✅ FIXED: Use Form() with explicit default  
    tier: str = Form(default="standard")       # ✅ FIXED: Use Form() with explicit default
):
    """
    Translate large documents (PDF, TXT, DOC, DOCX)
    
    Args:
        file: PDF, TXT, DOC, or DOCX file to translate
        source_lang: Source language code (auto, en, vi, etc.)
        target_lang: Target language code (vi, en, zh, etc.)
        tier: Translation tier (free, basic, standard, premium)
        
    Returns:
        Job ID and status
    """
    try:
        # ✅ DEBUG: Log exact parameters received from form
        logger.info(f"🔍 API FORM DEBUG - Raw Parameters Received:")
        logger.info(f"📁 file.filename: {file.filename}")
        logger.info(f"📁 file.content_type: {getattr(file, 'content_type', 'unknown')}")
        logger.info(f"🗣️ source_lang (raw): '{source_lang}' (type: {type(source_lang)})")
        logger.info(f"🎯 target_lang (raw): '{target_lang}' (type: {type(target_lang)})")  # ← Key debug
        logger.info(f"⭐ tier (raw): '{tier}' (type: {type(tier)})")
        
        # ✅ VALIDATION: Normalize and validate language parameters
        source_lang = source_lang.strip().lower() if source_lang else "auto"
        target_lang = target_lang.strip().lower() if target_lang else "vi"
        tier = tier.strip().lower() if tier else "standard"
        
        logger.info(f"🔧 NORMALIZED PARAMETERS:")
        logger.info(f"🗣️ source_lang (normalized): '{source_lang}'")
        logger.info(f"🎯 target_lang (normalized): '{target_lang}'")  # ← Should show 'en' when sent
        logger.info(f"⭐ tier (normalized): '{tier}'")
        
        # ✅ VALIDATION: Language code mapping
        language_mappings = {
            'en': 'en', 'english': 'en', 'eng': 'en',
            'vi': 'vi', 'vietnamese': 'vi', 'vie': 'vi',
            'zh': 'zh', 'chinese': 'zh', 'chi': 'zh',
            'ja': 'ja', 'japanese': 'ja', 'jpn': 'ja',
            'ko': 'ko', 'korean': 'ko', 'kor': 'ko',
            'fr': 'fr', 'french': 'fr', 'fra': 'fr',
            'de': 'de', 'german': 'de', 'deu': 'de',
            'es': 'es', 'spanish': 'es', 'spa': 'es',
            'auto': 'auto'
        }
        
        # Map languages to standard codes
        mapped_source = language_mappings.get(source_lang, source_lang)
        mapped_target = language_mappings.get(target_lang, target_lang)
        
        logger.info(f"🗺️ LANGUAGE MAPPING:")
        logger.info(f"🗣️ source: '{source_lang}' → '{mapped_source}'")
        logger.info(f"🎯 target: '{target_lang}' → '{mapped_target}'")  # ← Should show en
        
        # ✅ VALIDATION: File type check
        supported_extensions = ('.pdf', '.txt', '.doc', '.docx')
        if not file.filename or not file.filename.lower().endswith(supported_extensions):
            raise HTTPException(
                400, 
                {
                    "error": "Unsupported file type",
                    "message": f"Only PDF, TXT, DOC, and DOCX files are supported",
                    "received_file": file.filename or "No filename",
                    "supported_formats": ["PDF", "TXT", "DOC", "DOCX"]
                }
            )
        
        # Get file type information
        file_info = get_file_type_info(file.filename)
        logger.info(f"Processing {file_info['description']}: {file.filename}")
        
        # ✅ VALIDATION: File size check
        content = await file.read()
        file_size_mb = len(content) / (1024 * 1024)
        
        if file_size_mb > 100:
            raise HTTPException(413, {
                "error": "File too large",
                "message": f"File size: {file_size_mb:.1f}MB (max 100MB)",
                "max_size_mb": 100
            })
            
        if len(content) == 0:
            raise HTTPException(400, {
                "error": "Empty file",
                "message": "The uploaded file is empty",
            })
        
        # ✅ SAVE FILE: Create temp file with proper handling
        temp_dir = Path(tempfile.gettempdir()) / "prismy_uploads"
        temp_dir.mkdir(exist_ok=True)
        
        job_id = str(uuid.uuid4())
        temp_filename = f"{job_id}_{file.filename}"
        temp_path = temp_dir / temp_filename
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        logger.info(f"File saved: {temp_path} ({file_size_mb:.2f}MB)")
        
        # ✅ ESTIMATE PAGES: Get page count for different file types
        total_pages = 1  # Default
        
        try:
            file_extension = file.filename.lower().split('.')[-1]
            
            if file_extension == 'pdf':
                # Count PDF pages
                try:
                    import pdfplumber
                    with pdfplumber.open(temp_path) as pdf:
                        total_pages = len(pdf.pages)
                    logger.info(f"PDF pages detected: {total_pages}")
                except Exception as e:
                    logger.warning(f"Could not count PDF pages: {e}, using file size estimate")
                    total_pages = max(1, int(file_size_mb * 2))  # ~0.5MB per page estimate
                    
            elif file_extension in ['doc', 'docx']:
                # Estimate Word document pages
                # Rough estimate: 1 page ≈ 2-4KB for plain text content
                estimated_pages = max(1, int(file_size_mb * 1024 / 3))  # 3KB per page
                total_pages = min(estimated_pages, 500)  # Cap at 500 pages
                logger.info(f"Word document estimated pages: {total_pages}")
                
            elif file_extension == 'txt':
                # Text files are typically 1 "page"
                total_pages = 1
                
        except Exception as e:
            logger.warning(f"Page estimation failed: {e}")
            total_pages = max(1, int(file_size_mb))
        
        # ✅ PROCESSING TIME ESTIMATE
        estimate = estimate_processing_time(file_size_mb, file_info['type'], total_pages)
        
        # ✅ CREATE JOB: Store initial job data with MAPPED languages
        job_data = {
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "total_pages": total_pages,
            "file_type": file_info['type'],
            "file_extension": file_extension,
            "file_description": file_info['description'],
            "source_language": mapped_source,  # ✅ Use mapped language
            "target_language": mapped_target,  # ✅ Use mapped language
            "tier": tier,
            "file_size_mb": round(file_size_mb, 2),
            "original_filename": file.filename,
            "temp_file_path": str(temp_path),
            "estimated_time": estimate["formatted"],
            "message": f"Job created. Processing {file_info['description']}..."
        }
        
        logger.info(f"📋 JOB DATA CREATED:")
        logger.info(f"🗣️ source_language in job: '{job_data['source_language']}'")
        logger.info(f"🎯 target_language in job: '{job_data['target_language']}'")  # ← Should be 'en'
        
        # Store job data in Redis
        store_job_data_as_hash(job_id, job_data)
        
        # ✅ START CELERY TASK: Launch translation process
        try:
            logger.info(f"🚀 STARTING CELERY TASK:")
            logger.info(f"📁 File Path: {temp_path}")
            logger.info(f"📄 File Type: {file_info['celery_type']}")
            logger.info(f"🎯 Target Language → Celery: '{mapped_target}'")  # ← Should be 'en'
            logger.info(f"⭐ Tier: {tier}")
            
            # Use the fixed sync task with MAPPED target language
            task_result = process_translation_sync.apply_async(
                args=[job_id, str(temp_path), file_info['celery_type'], mapped_target, tier],
                #                                                        ↑ Use mapped_target
                queue='default'
            )
            
            # Update job with task ID
            job_data['celery_task_id'] = task_result.id
            store_job_data_as_hash(job_id, job_data)
            
            logger.info(f"✅ Celery task started: {task_result.id}")
            logger.info(f"🎯 FINAL CHECK - Task called with target_lang: '{mapped_target}'")
            
        except Exception as e:
            logger.error(f"❌ Failed to start Celery task: {e}")
            # Update job as failed
            job_data['status'] = JobStatus.FAILED.value
            job_data['error'] = f"Failed to start processing: {str(e)}"
            store_job_data_as_hash(job_id, job_data)
            
            raise HTTPException(500, {
                "error": "Processing failed",
                "message": f"Failed to start translation task: {str(e)}",
                "job_id": job_id
            })
        
        logger.info(f"Job created successfully: {job_id} for {file_info['description']} ({file_size_mb:.2f}MB)")
        
        # ✅ RETURN RESPONSE
        return JSONResponse({
            "job_id": job_id,
            "status": JobStatus.PENDING.value,
            "total_pages": total_pages,
            "file_type": file_info['type'],
            "file_description": file_info['description'],
            "estimated_time": estimate["formatted"],
            "message": f"Job created. Processing {file_info['description']}: {file.filename}...",
            "supported_formats": ["PDF", "TXT", "DOC", "DOCX"],
            # ✅ DEBUG: Include language info in response
            "debug_info": {
                "source_language": mapped_source,
                "target_language": mapped_target,
                "original_target_input": target_lang
            }
        })
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Unexpected error in translate_large_document: {e}")
        raise HTTPException(500, {
            "error": "Internal server error",
            "message": f"An unexpected error occurred: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        })

@router.get("/status/{job_id}")
async def get_job_status(job_id: str):
    """Get job status and progress"""
    try:
        # Get job data using hash operations
        data = get_job_data_from_hash(job_id)
        
        if not data:
            raise HTTPException(404, {
                "error": "Job not found",
                "job_id": job_id,
                "message": "The specified job ID does not exist or has expired"
            })
        
        # Return comprehensive job status
        return {
            "job_id": job_id,
            "status": data.get("status", "unknown"),
            "progress": int(data.get("progress", 0)),
            "total_pages": int(data.get("total_pages", 0)),
            "file_type": data.get("file_type", "unknown"),
            "file_extension": data.get("file_extension", ""),
            "file_description": data.get("file_description", "Unknown File"),
            "source_language": data.get("source_language"),
            "target_language": data.get("target_language"),
            "tier": data.get("tier"),
            "error": data.get("error", ""),
            "output_file": data.get("output_file", ""),
            "message": data.get("message", ""),
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at"),
            "estimated_time": data.get("estimated_time", "Unknown"),
            "file_size_mb": float(data.get("file_size_mb", 0)),
            "celery_task_id": data.get("celery_task_id", "")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job status for {job_id}: {e}")
        raise HTTPException(500, {
            "error": "Status check failed",
            "message": f"Could not retrieve job status: {str(e)}",
            "job_id": job_id
        })

@router.get("/download/{job_id}")
async def download_result(job_id: str):
    """Download translation result"""
    try:
        # Get job data using hash operations
        data = get_job_data_from_hash(job_id)
        
        if not data:
            raise HTTPException(404, {
                "error": "Job not found",
                "job_id": job_id,
                "message": "The specified job ID does not exist or has expired"
            })
        
        # Check job status
        status = data.get("status", "unknown")
        if status != "completed":
            if status == "failed":
                error_msg = data.get("error", "Unknown error")
                raise HTTPException(400, {
                    "error": "Job failed",
                    "message": f"Translation failed: {error_msg}",
                    "job_id": job_id,
                    "status": status
                })
            else:
                raise HTTPException(400, {
                    "error": "Job not completed",
                    "message": f"Job is still {status}. Please wait for completion.",
                    "job_id": job_id,
                    "status": status,
                    "progress": data.get("progress", 0)
                })
        
        # Get file paths
        output_file = data.get('output_file')
        output_path = data.get('output_path')
        original_filename = data.get('original_filename', 'translated_document')
        
        # Try to find the output file
        file_path = None
        
        # Method 1: Try output_path directly
        if output_path and Path(output_path).exists():
            file_path = output_path
            logger.info(f"Found file at output_path: {file_path}")
        
        # Method 2: Try output_file in common directories
        elif output_file:
            possible_dirs = [
                os.environ.get("OUTPUT_DIR", "outputs"),
                "outputs",
                "storage/outputs", 
                "/tmp",
                tempfile.gettempdir()
            ]
            
            for base_dir in possible_dirs:
                potential_path = Path(base_dir) / output_file
                if potential_path.exists():
                    file_path = str(potential_path)
                    logger.info(f"Found file at: {file_path}")
                    break
        
        # Method 3: Search for file with job_id pattern
        if not file_path:
            search_dirs = ["outputs", "storage/outputs", tempfile.gettempdir()]
            search_pattern = f"translated_{job_id}.*"
            
            for search_dir in search_dirs:
                search_path = Path(search_dir)
                if search_path.exists():
                    import glob
                    matches = glob.glob(str(search_path / search_pattern))
                    if matches:
                        file_path = matches[0]
                        logger.info(f"Found file by pattern: {file_path}")
                        break
        
        if not file_path or not Path(file_path).exists():
            raise HTTPException(404, {
                "error": "Output file not found",
                "message": "Translation completed but output file is missing",
                "job_id": job_id,
                "searched_paths": [output_path, output_file] if output_path or output_file else [],
                "status": status
            })
        
        # Generate appropriate download filename
        base_name = Path(original_filename).stem if original_filename else "translated_document"
        file_ext = Path(file_path).suffix or ".txt"
        download_filename = f"translated_{base_name}{file_ext}"
        
        # Determine media type
        media_type = 'text/plain; charset=utf-8'
        if file_ext == '.pdf':
            media_type = 'application/pdf'
        
        logger.info(f"📥 Serving download: {download_filename} from {file_path}")
        
        # Return file for download
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=download_filename,
            headers={
                "Content-Disposition": f'attachment; filename="{download_filename}"',
                "Content-Type": media_type,
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Download error for job {job_id}: {e}")
        raise HTTPException(500, {
            "error": "Download failed",
            "message": f"Could not serve download: {str(e)}",
            "job_id": job_id
        })

@router.get("/queue/status")
async def get_queue_status():
    """Get queue status and active jobs"""
    try:
        r = get_redis_client()
        
        # Get all job keys
        job_keys = r.keys("prismy:job:*")
        
        # Categorize jobs by status
        status_counts = {
            "pending": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "total": len(job_keys)
        }
        
        active_jobs = []
        
        for job_key in job_keys[:10]:  # Limit to 10 recent jobs
            job_data = r.hgetall(job_key)
            if job_data:
                job_id = job_key.split(":")[-1]
                status = job_data.get("status", "unknown")
                
                # Update counts
                if status in status_counts:
                    status_counts[status] += 1
                
                # Add to active jobs if not completed
                if status in ["pending", "processing"]:
                    active_jobs.append({
                        "job_id": job_id,
                        "status": status,
                        "progress": f"{job_data.get('progress', 0)}%",
                        "file_type": job_data.get("file_type", "unknown"),
                        "created_at": job_data.get("created_at", "")
                    })
        
        return {
            "queue_status": "healthy",
            "statistics": status_counts,
            "active_jobs": active_jobs,
            "redis_connected": True,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting queue status: {e}")
        return {
            "queue_status": "error",
            "statistics": {"error": str(e)},
            "active_jobs": [],
            "redis_connected": False,
            "timestamp": datetime.utcnow().isoformat()
        }

@router.post("/cancel/{job_id}")
async def cancel_job(job_id: str):
    """Cancel a job"""
    try:
        data = get_job_data_from_hash(job_id)
        
        if not data:
            raise HTTPException(404, "Job not found")
        
        status = data.get("status", "unknown")
        if status == "completed":
            raise HTTPException(400, "Cannot cancel completed job")
        
        if status == "failed":
            raise HTTPException(400, "Job already failed")
        
        # Cancel Celery task if it exists
        celery_task_id = data.get("celery_task_id")
        if celery_task_id:
            try:
                from celery_app import app as celery_app
                celery_app.control.revoke(celery_task_id, terminate=True)
                logger.info(f"Cancelled Celery task: {celery_task_id}")
            except Exception as e:
                logger.warning(f"Could not cancel Celery task {celery_task_id}: {e}")
        
        # Update job status
        r = get_redis_client()
        r.hset(f"prismy:job:{job_id}", mapping={
            "status": "cancelled",
            "error": "Cancelled by user",
            "updated_at": datetime.utcnow().isoformat(),
            "progress": 0
        })
        
        logger.info(f"Job cancelled: {job_id}")
        
        return {
            "message": "Job cancelled successfully",
            "job_id": job_id,
            "previous_status": status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling job {job_id}: {e}")
        raise HTTPException(500, f"Failed to cancel job: {str(e)}")

@router.get("/debug/{job_id}")
async def debug_job(job_id: str):
    """Debug endpoint to inspect job data - useful for troubleshooting"""
    try:
        r = get_redis_client()
        
        # Check both hash and string formats
        hash_data = r.hgetall(f"prismy:job:{job_id}")
        string_data = r.get(f"prismy:job:{job_id}")
        key_type = r.type(f"prismy:job:{job_id}")
        key_exists = r.exists(f"prismy:job:{job_id}")
        ttl = r.ttl(f"prismy:job:{job_id}")
        
        # Check for output files
        output_file_paths = []
        if hash_data:
            output_file = hash_data.get('output_file')
            output_path = hash_data.get('output_path')
            
            if output_file:
                for base_dir in ["outputs", "storage/outputs", "/tmp"]:
                    potential_path = Path(base_dir) / output_file
                    output_file_paths.append({
                        "path": str(potential_path),
                        "exists": potential_path.exists(),
                        "size": potential_path.stat().st_size if potential_path.exists() else 0
                    })
            
            if output_path:
                output_file_paths.append({
                    "path": output_path,
                    "exists": Path(output_path).exists() if output_path else False,
                    "size": Path(output_path).stat().st_size if output_path and Path(output_path).exists() else 0
                })
        
        return {
            "job_id": job_id,
            "redis_info": {
                "key_exists": bool(key_exists),
                "key_type": key_type,
                "ttl_seconds": ttl,
                "hash_field_count": len(hash_data) if hash_data else 0
            },
            "job_data": {
                "hash_format": hash_data if hash_data else None,
                "string_format": string_data if string_data else None
            },
            "output_files": output_file_paths,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Debug error for job {job_id}: {e}")
        return {
            "job_id": job_id,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

@router.get("/supported-formats")
async def get_supported_formats():
    """Get list of supported file formats"""
    return {
        "supported_formats": [
            {
                "extension": "pdf",
                "description": "PDF Document",
                "mime_types": ["application/pdf"],
                "max_size_mb": 100,
                "features": ["Text extraction", "Table extraction", "OCR support"]
            },
            {
                "extension": "docx",
                "description": "Word 2007+ Document",
                "mime_types": ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"],
                "max_size_mb": 100,
                "features": ["Paragraph extraction", "Table extraction", "Formatting preservation"]
            },
            {
                "extension": "doc",
                "description": "Word 97-2003 Document",
                "mime_types": ["application/msword"],
                "max_size_mb": 100,
                "features": ["Basic text extraction", "Converted to DOCX format"]
            },
            {
                "extension": "txt",
                "description": "Text Document",
                "mime_types": ["text/plain"],
                "max_size_mb": 100,
                "features": ["Plain text processing", "Multiple encoding support"]
            }
        ],
        "total_formats": 4,
        "max_file_size_mb": 100,
        "supported_languages": {
            "source": ["auto", "en", "vi", "zh", "ja", "ko", "fr", "de", "es"],
            "target": ["vi", "en", "zh", "ja", "ko", "fr", "de", "es"]
        },
        "translation_tiers": ["free", "basic", "standard", "premium"]
    }

def include_large_document_routes(app):
    """Include large document routes in main app"""
    app.include_router(router, prefix="/api/v1/large", tags=["Large Documents"])