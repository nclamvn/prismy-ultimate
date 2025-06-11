import fitz
import redis
from celery import Task
from typing import List, Dict
import json
from datetime import datetime
from celery_app import app
from ..utils.pdf_advanced import AdvancedPDFExtractor
from .translation_apis import translate_with_tier

redis_client = redis.Redis(host='localhost', port=6379, decode_responses=True)

class PDFProcessorTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = args[0]
        redis_client.hset(f"job:{job_id}", mapping={
            "status": "failed",
            "error": str(exc),
            "progress": -1
        })

def extract_pdf_chunks(file_path: str, chunk_size: int = 1000) -> List[Dict]:
    """Extract text from PDF with OCR support"""
    extractor = AdvancedPDFExtractor()
    doc = fitz.open(file_path)
    all_chunks = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract content with OCR if needed
        page_content = extractor.extract_page_content(page, page_num)
        
        # Smart chunk the text
        text_chunks = extractor.smart_chunk_text(page_content['text'], chunk_size)
        
        for i, chunk_text in enumerate(text_chunks):
            all_chunks.append({
                'text': chunk_text,
                'page_num': page_num,
                'chunk_id': len(all_chunks),
                'is_scanned': page_content['is_scanned'],
                'has_images': len(page_content['images']) > 0
            })
    
    doc.close()
    return all_chunks

def translate_chunk(text: str, source_lang: str, target_lang: str, tier: str) -> str:
    """Use real translation API"""
    return translate_with_tier(text, source_lang, target_lang, tier)

def reconstruct_translated_pdf(job_id: str, original_path: str) -> str:
    """Create output with translations"""
    output_path = f"/tmp/translated_{job_id}.txt"
    
    # Get all chunks
    chunks = []
    i = 0
    while True:
        chunk_data = redis_client.get(f"job:{job_id}:chunk:{i}")
        if not chunk_data:
            break
        chunks.append(json.loads(chunk_data))
        i += 1
    
    # Get job info
    job_info = redis_client.hgetall(f"job:{job_id}")
    
    # Group by page
    pages = {}
    for chunk in chunks:
        page_num = chunk['page_num']
        if page_num not in pages:
            pages[page_num] = []
        pages[page_num].append(chunk)
    
    # Write formatted output
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("="*60 + "\n")
        f.write("PRISMY Translation Result\n")
        f.write("="*60 + "\n")
        f.write(f"Job ID: {job_id}\n")
        f.write(f"Source Language: {job_info.get('source_lang', 'auto')}\n")
        f.write(f"Target Language: {job_info.get('target_lang', 'unknown')}\n")
        f.write(f"Translation Tier: {job_info.get('tier', 'unknown').upper()}\n")
        f.write(f"Total Pages: {len(pages)}\n")
        f.write("="*60 + "\n\n")
        
        for page_num in sorted(pages.keys()):
            f.write(f"\n{'='*20} Page {page_num + 1} {'='*20}\n")
            if pages[page_num][0].get('is_scanned'):
                f.write("[Note: This page was processed with OCR]\n")
            f.write("\n")
            
            # Write original and translation
            for chunk in pages[page_num]:
                # Original
                f.write("Original:\n")
                f.write("-" * 40 + "\n")
                f.write(chunk['text'] + "\n\n")
                
                # Translation
                f.write("Translation:\n")
                f.write("-" * 40 + "\n")
                f.write(chunk['translated'] + "\n\n")
                f.write("="*60 + "\n\n")
    
    return output_path

@app.task(bind=True, base=PDFProcessorTask, max_retries=3)
def process_pdf_translation(self, job_id: str, file_path: str, options: Dict):
    """Process PDF with real translation"""
    try:
        # Update status
        redis_client.hset(f"job:{job_id}", mapping={
            "status": "processing",
            "progress": 0,
            "start_time": datetime.now().isoformat(),
            "source_lang": options.get('source_lang', 'auto'),
            "target_lang": options.get('target_lang', 'en'),
            "tier": options.get('tier', 'standard')
        })
        
        # Extract chunks with OCR
        chunks = extract_pdf_chunks(file_path, options.get('chunk_size', 1000))
        total_chunks = len(chunks)
        
        # Store metadata
        redis_client.hset(f"job:{job_id}", mapping={
            "total_chunks": total_chunks,
            "total_pages": chunks[-1]['page_num'] + 1 if chunks else 0
        })
        
        # Process each chunk
        for i, chunk in enumerate(chunks):
            chunk_key = f"job:{job_id}:chunk:{i}"
            
            # Translate chunk
            translated = translate_chunk(
                chunk['text'], 
                options['source_lang'],
                options['target_lang'],
                options['tier']
            )
            
            # Store result with metadata
            redis_client.setex(
                chunk_key,
                86400,  # 24 hours TTL
                json.dumps({
                    **chunk,
                    'translated': translated
                })
            )
            
            # Update progress
            progress = int((i + 1) / total_chunks * 100)
            redis_client.hset(f"job:{job_id}", "progress", progress)
        
        # Create output
        output_path = reconstruct_translated_pdf(job_id, file_path)
        
        # Final update
        redis_client.hset(f"job:{job_id}", mapping={
            "status": "completed",
            "output_path": output_path,
            "progress": 100,
            "end_time": datetime.now().isoformat()
        })
        
        return {"job_id": job_id, "output_path": output_path}
        
    except Exception as exc:
        self.retry(exc=exc, countdown=60 * (self.request.retries + 1))
