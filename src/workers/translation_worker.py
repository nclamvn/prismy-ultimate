# src/workers/translation_worker.py

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class TranslationWorker:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.use_mock = True
        
    async def connect(self):
        """Connect to Redis"""
        self.redis_client = await redis.from_url(self.redis_url)
        logger.info("Connected to Redis")
    
    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()
    
    async def get_job_data(self, job_id: str) -> Dict[str, Any]:
        """Get job data from Redis"""
        job_key = f"prismy:job:{job_id}"
        job_data = await self.redis_client.hgetall(job_key)
        
        if not job_data:
            raise ValueError(f"Job not found: {job_id}")
        
        return {
            'job_id': job_id,
            'source_lang': job_data.get(b'source_lang', b'vi').decode('utf-8'),
            'target_lang': job_data.get(b'target_lang', b'en').decode('utf-8'),
            'tier': job_data.get(b'tier', b'standard').decode('utf-8')
        }
    
    async def process_translation_job(self, job_data: Dict[str, Any]):
        """Process a single translation job"""
        job_id = job_data['job_id']
        source_lang = job_data.get('source_lang', 'auto')
        target_lang = job_data.get('target_lang', 'en')
        
        logger.info(f"Processing translation job: {job_id}")
        
        try:
            # Update status
            await self._update_job_status(job_id, "translation", "processing")
            
            # Get all chunks
            chunks = await self._get_chunks(job_id)
            
            if not chunks:
                logger.warning(f"No chunks found for job {job_id}, skipping to reconstruction")
                # Still move to reconstruction even with no chunks
                await self._update_job_status(job_id, "translation", "completed")
                await self.redis_client.rpush("prismy:reconstruct", job_id)
                return
            
            # Translate chunks
            translated_count = 0
            
            for chunk in chunks:
                chunk_id = chunk['chunk_id']
                
                # Translate based on chunk type
                if chunk['type'] == 'table':
                    translated_text = await self._translate_table(chunk['text'], source_lang, target_lang)
                elif chunk['type'] == 'formula':
                    translated_text = chunk['text']
                else:
                    translated_text = await self._translate_text(chunk['text'], source_lang, target_lang)
                
                # Store translated chunk
                translated_chunk = {
                    **chunk,
                    'translated_text': translated_text,
                    'source_lang': source_lang,
                    'target_lang': target_lang,
                    'translated_at': datetime.now().isoformat()
                }
                
                await self.redis_client.setex(
                    f"translated:{job_id}:{chunk_id}",
                    86400,
                    json.dumps(translated_chunk)
                )
                
                translated_count += 1
            
            # Update count
            await self.redis_client.set(
                f"count:translated:{job_id}",
                translated_count
            )
            
            # Mark translation complete
            await self._update_job_status(job_id, "translation", "completed")
            
            # Add to reconstruction queue
            await self.redis_client.rpush("prismy:reconstruct", job_id)
            
            logger.info(f"Translation completed for job {job_id}: {translated_count} chunks")
            
        except Exception as e:
            logger.error(f"Translation failed for job {job_id}: {str(e)}")
            await self._update_job_status(job_id, "translation", "failed", str(e))
    
    async def _get_chunks(self, job_id: str) -> List[Dict]:
        """Get all chunks from Redis"""
        chunks = []
        cursor = '0'
        
        while cursor != 0:
            cursor, keys = await self.redis_client.scan(
                cursor,
                match=f"chunked:{job_id}:*",
                count=100
            )
            
            if keys:
                values = await self.redis_client.mget(keys)
                for value in values:
                    if value:
                        chunks.append(json.loads(value))
        
        chunks.sort(key=lambda x: x.get('chunk_id', 0))
        return chunks
    
    async def _translate_text(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate regular text"""
        if not text or not text.strip():
            return text
        
        if self.use_mock:
            return f"[TRANSLATED from {source_lang} to {target_lang}]: {text}"
        
        return text
    
    async def _translate_table(self, table_json: str, source_lang: str, target_lang: str) -> str:
        """Translate table data"""
        try:
            table_data = json.loads(table_json)
            translated_data = []
            
            for row in table_data:
                translated_row = []
                for cell in row:
                    if cell and isinstance(cell, str):
                        translated_cell = await self._translate_text(cell, source_lang, target_lang)
                        translated_row.append(translated_cell)
                    else:
                        translated_row.append(cell)
                translated_data.append(translated_row)
            
            return json.dumps(translated_data)
        except Exception as e:
            logger.error(f"Table translation error: {e}")
            return table_json
    
    async def _update_job_status(self, job_id: str, stage: str, status: str, error: str = None):
        """Update job status in Redis"""
        status_data = {
            'job_id': job_id,
            'stage': stage,
            'status': status,
            'updated_at': datetime.now().isoformat()
        }
        
        if error:
            status_data['error'] = error
        
        await self.redis_client.hset(
            f"job:{job_id}",
            stage,
            json.dumps(status_data)
        )
    
    async def run(self):
        """Main worker loop"""
        await self.connect()
        
        logger.info("Translation worker started (using MOCK translator)")
        
        try:
            while True:
                # Get job_id from queue
                result = await self.redis_client.blpop("prismy:translate", timeout=5)
                
                if result:
                    _, job_id_bytes = result
                    job_id = job_id_bytes.decode('utf-8')
                    
                    try:
                        job_data = await self.get_job_data(job_id)
                        await self.process_translation_job(job_data)
                    except Exception as e:
                        logger.error(f"Failed to process job {job_id}: {e}")
                        
        except KeyboardInterrupt:
            logger.info("Worker stopped by user")
        finally:
            await self.disconnect()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    worker = TranslationWorker()
    asyncio.run(worker.run())
