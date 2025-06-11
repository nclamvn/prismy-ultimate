"""
Translation API endpoint with storage
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
import os
from datetime import datetime
import logging

from ...modules.extraction.pdf_extractor import PDFExtractor
from ...services.translation_service import translation_service, TranslationTier
from ...services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["translation"])

@router.post("/translate")
async def translate_document(
    file: UploadFile = File(...),
    target_language: str = Form("vi"),
    quality_tier: str = Form("basic")
):
    """Translate uploaded document"""
    try:
        # Validate
        if not file.filename.endswith('.pdf'):
            raise HTTPException(400, "Only PDF files are supported")
            
        try:
            tier = TranslationTier(quality_tier)
        except ValueError:
            tier = TranslationTier.BASIC
            
        # Save upload
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_data = await file.read()
        file_path = await storage_service.save_upload(file_data, filename)
        
        logger.info(f"Processing: {filename} with {tier.value} tier")
        
        # Extract
        extractor = PDFExtractor()
        extracted_text = extractor.extract(file_path)
        
        # Translate
        result = await translation_service.translate(
            text=extracted_text[:2000],  # Limit for testing
            target_lang=target_language,
            tier=tier
        )
        
        # Save result (for now as text)
        output_filename = f"translated_{timestamp}_{target_language}.txt"
        output_path = await storage_service.save_output(
            result["translated_text"].encode('utf-8'),
            output_filename
        )
        
        return {
            "status": "success" if result["success"] else "error",
            "job_id": timestamp,
            "original_file": file.filename,
            "file_size": storage_service.get_file_size(file_path),
            "target_language": target_language,
            "quality_tier": tier.value,
            "preview": result["translated_text"][:500],
            "cost_estimate": result.get("cost", 0),
            "output_file": output_filename
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/download/{filename}")
async def download_result(filename: str):
    """Download translated file"""
    file_path = storage_service.outputs_dir / filename
    
    if not file_path.exists():
        raise HTTPException(404, "File not found")
        
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/octet-stream'
    )

@router.get("/supported-languages")
async def get_supported_languages():
    """Get list of supported languages"""
    return {
        "languages": [
            {"code": "vi", "name": "Vietnamese"},
            {"code": "en", "name": "English"}, 
            {"code": "zh", "name": "Chinese"},
            {"code": "ja", "name": "Japanese"},
            {"code": "ko", "name": "Korean"},
            {"code": "fr", "name": "French"},
            {"code": "es", "name": "Spanish"},
            {"code": "de", "name": "German"}
        ]
    }

@router.get("/quality-tiers")
async def get_quality_tiers():
    """Get available quality tiers"""
    return {
        "tiers": [
            {
                "id": "basic",
                "name": "Basic",
                "description": "Fast, simple translation",
                "cost_per_page": 0.01,
                "eta_minutes": 1
            },
            {
                "id": "standard", 
                "name": "Standard",
                "description": "Balanced quality and speed",
                "cost_per_page": 0.05,
                "eta_minutes": 5
            },
            {
                "id": "premium",
                "name": "Premium", 
                "description": "Highest quality with review",
                "cost_per_page": 0.15,
                "eta_minutes": 10
            }
        ]
    }
