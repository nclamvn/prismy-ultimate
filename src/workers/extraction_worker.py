# src/workers/extraction_worker.py

import asyncio
import json
import logging
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

import redis.asyncio as redis
from src.modules.extraction.v2.streaming_extractor import StreamingPDFExtractor
from src.modules.extraction.enhanced_extractor import EnhancedPDFExtractor

logger = logging.getLogger(__name__)

class PDFExtractionWorker:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.extractor = EnhancedPDFExtractor(use_ocr=False)
        
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
        
        # Convert bytes to string and create dict
        return {
            'job_id': job_id,
            'file_path': job_data.get(b'file_path', b'').decode('utf-8'),
            'source_lang': job_data.get(b'source_lang', b'vi').decode('utf-8'),
            'target_lang': job_data.get(b'target_lang', b'en').decode('utf-8'),
            'tier': job_data.get(b'tier', b'standard').decode('utf-8')
        }
    
    async def process_extraction_job(self, job_data: Dict[str, Any]):
        """Process a single extraction job"""
        job_id = job_data['job_id']
        file_path = job_data['file_path']
        
        logger.info(f"Processing extraction job: {job_id}")
        
        try:
            # Update status
            await self._update_job_status(job_id, "extraction", "processing")
            
            # Extract PDF using streaming
            batch_count = 0
            element_count = 0
            
            # Use process_streaming async method
            async for batch_data in self.extractor.process_streaming(file_path):
                batch_count += 1
                
                # Store the entire batch
                batch_key = f"batch:{job_id}:{batch_count}"
                await self.redis_client.setex(
                    batch_key,
                    86400,  # 24 hours
                    json.dumps(batch_data)
                )
                
                # Count elements
                if 'content' in batch_data:
                    for page_data in batch_data['content']:
                        element_count += len(page_data.get('elements', []))
                
                # Update progress
                await self.redis_client.set(
                    f"count:extracted:{job_id}",
                    element_count
                )
                
                logger.info(f"Processed batch {batch_count}")
            
            # Mark extraction complete and move to chunking
            await self._update_job_status(job_id, "extraction", "completed")
            
            # Add to chunking queue - push job_id only
            await self.redis_client.rpush(
                "prismy:chunk",
                job_id
            )
            
            logger.info(f"Extraction completed for job {job_id}: {batch_count} batches, {element_count} elements")
            
        except Exception as e:
            logger.error(f"Extraction failed for job {job_id}: {str(e)}")
            await self._update_job_status(job_id, "extraction", "failed", str(e))
    
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
        
        logger.info("Extraction worker started")
        
        try:
            while True:
                # Get job_id from queue
                result = await self.redis_client.blpop("prismy:extract", timeout=5)
                
                if result:
                    _, job_id_bytes = result
                    job_id = job_id_bytes.decode('utf-8')
                    
                    try:
                        # Get full job data
                        job_data = await self.get_job_data(job_id)
                        await self.process_extraction_job(job_data)
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
    
    worker = PDFExtractionWorker()
    asyncio.run(worker.run())
