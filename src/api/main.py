"""
PRISMY Translation API - Production Version
No mock, no demo - Real functionality only
"""
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from src.api import celery_endpoints
import openai
import os
import pdfplumber
import tempfile
import uuid
from datetime import datetime

from .v1.large_document import router as large_document_router

app = FastAPI(title="PRISMY Translation API", version="1.0.0")

# CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Specific origin
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# OpenAI client
openai.api_key = os.getenv("OPENAI_API_KEY")

# Storage for complete translations (in production, use database)
translation_storage = {}

# Include large document routes
app.include_router(large_document_router)
app.include_router(celery_endpoints.router, prefix="/api/v2", tags=["Async Translation"])

@app.get("/")
def root():
    return {
        "service": "PRISMY Translation API",
        "version": "1.0.0",
        "status": "operational"
    }

@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.post("/translate")
async def translate_pdf(file: UploadFile = File(...)):
    """
    Extract and translate PDF - Production endpoint
    Returns complete text, not preview
    """
    if not file.filename.endswith('.pdf'):
        return JSONResponse(status_code=400, content={"error": "Only PDF files accepted"})
    
    # Generate unique ID for this translation
    translation_id = str(uuid.uuid4())
    
    # Save uploaded file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Extract complete text
        full_text = ""
        total_pages = 0
        
        with pdfplumber.open(tmp_path) as pdf:
            total_pages = len(pdf.pages)
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    full_text += f"\n--- Page {i+1} ---\n{page_text}\n"
        
        # Translate complete text
        translated_text = ""
        if full_text and openai.api_key:
            # Split into manageable chunks
            chunk_size = 3000
            chunks = [full_text[i:i+chunk_size] for i in range(0, len(full_text), chunk_size)]
            
            for i, chunk in enumerate(chunks):
                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Translate to Vietnamese. Preserve formatting."},
                            {"role": "user", "content": chunk}
                        ],
                        max_tokens=2000
                    )
                    translated_text += response.choices[0].message.content + "\n\n"
                except Exception as e:
                    translated_text += f"\n[Translation error in chunk {i+1}: {str(e)}]\n"
        
        # Store complete translation
        translation_storage[translation_id] = {
            "filename": file.filename,
            "original": full_text,
            "translated": translated_text,
            "pages": total_pages,
            "timestamp": datetime.now().isoformat()
        }
        
        # Return complete data
        return {
            "id": translation_id,
            "filename": file.filename,
            "pages": total_pages,
            "original_length": len(full_text),
            "translated_length": len(translated_text),
            "original": full_text,
            "translated": translated_text
        }
        
    finally:
        # Cleanup
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

@app.get("/download/{translation_id}/{content_type}")
async def download_translation(translation_id: str, content_type: str):
    """
    Download original or translated text
    """
    if translation_id not in translation_storage:
        return JSONResponse(status_code=404, content={"error": "Translation not found"})
    
    data = translation_storage[translation_id]
    filename = data["filename"].replace('.pdf', '')
    
    if content_type == "original":
        content = data["original"]
        output_filename = f"{filename}_original.txt"
    else:
        content = data["translated"]
        output_filename = f"{filename}_vietnamese.txt"
    
    # Create temp file for download
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    return FileResponse(tmp_path, filename=output_filename, media_type='text/plain')

if __name__ == "__main__":
    import uvicorn
    print("PRISMY Translation API - Production")
    print("=" * 50)
    uvicorn.run(app, host="0.0.0.0", port=8000)
# Import and mount download fix router
from .v1.download_fix import create_fixed_download_endpoint
large_document_router = create_fixed_download_endpoint(large_document_router)
