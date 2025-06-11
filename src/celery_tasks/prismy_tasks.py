from celery import Task
from celery_app import app
import json
from typing import Dict, Any
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.workers.extraction_worker import PDFExtractionWorker
from src.workers.translation_worker import TranslationWorker
from src.workers.reconstruction_worker import PDFReconstructionWorker
from src.services.queue.celery_manager import CeleryQueueManager

queue_manager = CeleryQueueManager()

class CallbackTask(Task):
    def on_success(self, retval, task_id, args, kwargs):
        job_id = kwargs.get('job_id')
        if job_id:
            queue_manager.update_job_status(job_id, 'completed', retval)
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        job_id = kwargs.get('job_id')
        if job_id:
            queue_manager.update_job_status(job_id, 'failed', {'error': str(exc)})

@app.task(name='prismy.extract', base=CallbackTask, bind=True)
def extract_document(self, job_data: Dict[str, Any], job_id: str = None):
    try:
        self.update_state(state='PROCESSING', meta={'stage': 'extraction'})
        
        file_path = job_data.get('file_path')
        file_type = job_data.get('file_type', 'pdf')
        
        if file_type == 'text':
            # For text files, just read and pass through
            with open(file_path, 'r', encoding='utf-8') as f:
                text_content = f.read()
            
            result = {
                'success': True,
                'text': text_content,
                'chunks': [{'text': text_content, 'page': 1}]
            }
        else:
            # For PDFs, use mock extraction for testing
            result = {
                'success': True,
                'chunks': [
                    {'text': 'This is a test PDF document.', 'page': 1},
                    {'text': 'Page 2 content goes here.', 'page': 2}
                ],
                'text': 'This is a test PDF document.\n\nPage 2 content goes here.'
            }
        
        if result:
            translation_data = {
                'job_id': job_id,
                'extraction_result': result,
                'source_file': file_path,
                'target_language': job_data['target_language'],
                'tier': job_data.get('tier', 'basic')
            }
            translate_document.apply_async(
                args=[translation_data],
                kwargs={'job_id': job_id},
                queue='translation'
            )
        
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.task(name='prismy.translate', base=CallbackTask, bind=True)
def translate_document(self, job_data: Dict[str, Any], job_id: str = None):
    try:
        self.update_state(state='PROCESSING', meta={'stage': 'translation'})
        
        extraction_result = job_data.get('extraction_result', {})
        chunks = extraction_result.get('chunks', [])
        if not chunks and 'text' in extraction_result:
            chunks = [{'text': extraction_result['text'], 'page': 1}]
        
        # Simple mock translation for testing
        translated_chunks = []
        for chunk in chunks:
            translated_text = f"[VI] {chunk['text']}"  # Mock Vietnamese translation
            translated_chunks.append({
                'original': chunk['text'],
                'translated': translated_text,
                'page': chunk.get('page', 1)
            })
        
        result = {
            'success': True,
            'translated_chunks': translated_chunks,
            'target_language': job_data['target_language']
        }
        
        # Continue to reconstruction
        reconstruction_data = {
            'job_id': job_id,
            'translation_result': result,
            'extraction_result': extraction_result,
            'source_file': job_data['source_file']
        }
        reconstruct_document.apply_async(
            args=[reconstruction_data],
            kwargs={'job_id': job_id},
            queue='reconstruction'
        )
        
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.task(name='prismy.reconstruct', base=CallbackTask, bind=True)
def reconstruct_document(self, job_data: Dict[str, Any], job_id: str = None):
    try:
        self.update_state(state='PROCESSING', meta={'stage': 'reconstruction'})
        
        source_file = job_data.get('source_file', '')
        translated_chunks = job_data.get('translation_result', {}).get('translated_chunks', [])
        
        # Simple reconstruction - just save translated text
        if source_file.endswith('.txt'):
            output_file = source_file.replace('.txt', '_translated.txt')
            translated_text = '\n\n'.join([chunk['translated'] for chunk in translated_chunks])
        else:
            # For PDF, save as text file for now
            output_file = source_file.replace('.pdf', '_translated.txt')
            translated_text = '\n\n'.join([
                f"Page {chunk['page']}:\n{chunk['translated']}" 
                for chunk in translated_chunks
            ])
        
        # Save the translated content
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(translated_text)
        
        result = {
            'success': True,
            'output_file': output_file
        }
        
        # Update job status with download URL
        if result.get('success'):
            queue_manager.update_job_status(
                job_id, 
                'completed',
                {
                    'output_file': result.get('output_file'),
                    'download_url': f'/api/v2/translate/job/{job_id}/download'
                }
            )
        
        return result
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.task(name='prismy.process_pdf')
def process_pdf_async(file_path: str, target_language: str, tier: str = 'basic') -> str:
    job_id = queue_manager.create_job({
        'file_path': file_path,
        'target_language': target_language,
        'tier': tier,
        'type': 'pdf_translation'
    })
    
    extract_document.apply_async(
        args=[{
            'file_path': file_path,
            'target_language': target_language,
            'tier': tier
        }],
        kwargs={'job_id': job_id},
        queue='extraction'
    )
    
    return job_id
