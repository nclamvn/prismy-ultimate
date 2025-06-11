"""
Advanced Translation API Endpoint
Uses Advanced PDF Processing
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import Optional
import logging

from ...modules.extraction.advanced import AdvancedPDFProcessor
from ...services.translation_service import translation_service, TranslationTier
from ...services.storage_service import storage_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/advanced", tags=["advanced-translation"])

@router.post("/translate")
async def translate_document_advanced(
    file: UploadFile = File(...),
    target_language: str = Form("vi"),
    quality_tier: str = Form("standard"),
    preserve_layout: bool = Form(True),
    extract_tables: bool = Form(True),
    extract_images: bool = Form(True)
):
    """
    Advanced translation with full document intelligence
    - Preserves layout and structure
    - Extracts and translates tables
    - Handles images with OCR option
    """
    try:
        # Initialize processors
        pdf_processor = AdvancedPDFProcessor({
            "extract_text": True,
            "preserve_layout": preserve_layout,
            "extract_tables": extract_tables,
            "extract_images": extract_images
        })
        
        # Save uploaded file
        file_data = await file.read()
        file_path = await storage_service.save_upload(file_data, file.filename)
        
        # Extract content
        extraction_result = await pdf_processor.process(file_path)
        
        # Translate text
        text = extraction_result.get('text', '')
        translation_result = await translation_service.translate(
            text=text,
            source_lang="auto",
            target_lang=target_language,
            tier=TranslationTier(quality_tier),
            use_chunking=True
        )
        
        # Prepare response
        return {
            "status": "success",
            "extraction": {
                "text_length": len(text),
                "tables": len(extraction_result.get('tables', [])),
                "images": len(extraction_result.get('images', [])),
                "pages": extraction_result.get('structure', {}).get('page_count', 0)
            },
            "translation": {
                "preview": translation_result['translated_text'][:500],
                "cost": translation_result.get('cost', 0),
                "chunks_used": translation_result.get('chunks_used', 1)
            },
            "capabilities_used": extraction_result['metadata']['capabilities_used']
        }
        
    except Exception as e:
        logger.error(f"Advanced translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/capabilities")
async def get_advanced_capabilities():
    """Get advanced processing capabilities"""
    processor = AdvancedPDFProcessor()
    info = processor.get_info()
    
    return {
        "version": info['version'],
        "capabilities": info['capabilities'],
        "extractors": info['extractors'],
        "features": {
            "layout_preservation": "Maintains document structure",
            "table_extraction": "Extracts tables with data structure",
            "image_extraction": "Extracts images with metadata",
            "ocr_ready": "Prepared for OCR processing",
            "smart_chunking": "Handles long documents intelligently"
        }
    }
