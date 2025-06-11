# src/workers/chunking_worker.py - Fixed for nested structure

import asyncio
import json
import logging
from typing import Dict, Any, List
from datetime import datetime

import redis.asyncio as redis

logger = logging.getLogger(__name__)

class ChunkingWorker:
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client = None
        self.chunk_size = 500  # characters per chunk
        
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
            'file_path': job_data.get(b'file_path', b'').decode('utf-8'),
            'source_lang': job_data.get(b'source_lang', b'vi').decode('utf-8'),
            'target_lang': job_data.get(b'target_lang', b'en').decode('utf-8'),
            'tier': job_data.get(b'tier', b'standard').decode('utf-8')
        }
    
    async def process_chunking_job(self, job_data: Dict[str, Any]):
        """Process a single chunking job"""
        job_id = job_data['job_id']
        
        logger.info(f"Processing chunking job: {job_id}")
        
        try:
            # Update status
            await self._update_job_status(job_id, "chunking", "processing")
            
            # Get all extracted batches
            batches = await self._get_extracted_batches(job_id)
            
            if not batches:
                raise ValueError("No extracted batches found")
            
            # Process batches into chunks
            chunks = self._create_chunks_from_batches(batches)
            
            # Store chunks
            for idx, chunk in enumerate(chunks):
                chunk_key = f"chunked:{job_id}:{idx}"
                await self.redis_client.setex(
                    chunk_key,
                    86400,  # 24 hours
                    json.dumps(chunk)
                )
            
            # Update count
            await self.redis_client.set(
                f"count:chunked:{job_id}",
                len(chunks)
            )
            
            # Mark chunking complete
            await self._update_job_status(job_id, "chunking", "completed")
            
            # Add to translation queue - push job_id
            await self.redis_client.rpush(
                "prismy:translate",
                job_id
            )
            
            logger.info(f"Chunking completed for job {job_id}: {len(chunks)} chunks")
            
        except Exception as e:
            logger.error(f"Chunking failed for job {job_id}: {str(e)}")
            await self._update_job_status(job_id, "chunking", "failed", str(e))
    
    async def _get_extracted_batches(self, job_id: str) -> List[Dict]:
        """Get all extracted batches from Redis"""
        batches = []
        cursor = '0'
        
        while cursor != 0:
            cursor, keys = await self.redis_client.scan(
                cursor,
                match=f"batch:{job_id}:*",
                count=100
            )
            
            if keys:
                values = await self.redis_client.mget(keys)
                for value in values:
                    if value:
                        batches.append(json.loads(value))
        
        return batches
    
    def _create_chunks_from_batches(self, batches: List[Dict]) -> List[Dict]:
        """Create chunks from batches - handle nested structure"""
        chunks = []
        current_chunk = {
            'text': '',
            'elements': [],
            'page_start': None,
            'page_end': None
        }
        
        for batch in batches:
            # Handle nested structure: batch.data.content or batch.content
            content_data = None
            
            if 'data' in batch and isinstance(batch['data'], dict):
                content_data = batch['data'].get('content', [])
            elif 'content' in batch:
                content_data = batch['content']
            
            if not content_data:
                logger.warning(f"No content found in batch: {batch.get('batch_id', 'unknown')}")
                continue
                
            # Process content
            for page_data in content_data:
                page_num = page_data.get('page', 0)
                
                for element in page_data.get('elements', []):
                    logger.debug(f"Processing element type: {element.get('type')}")
                    
                    # Handle different element types
                    if element['type'] in ['table', 'formula']:
                        # Save current chunk if not empty
                        if current_chunk['text']:
                            chunks.append(self._finalize_chunk(current_chunk, len(chunks)))
                            current_chunk = {'text': '', 'elements': [], 'page_start': None, 'page_end': None}
                        
                        # Create special chunk
                        special_chunk = {
                            'text': json.dumps(element.get('data', element.get('content', ''))),
                            'type': element['type'],
                            'elements': [element],
                            'page_start': page_num,
                            'page_end': page_num,
                            'metadata': element
                        }
                        chunks.append(self._finalize_chunk(special_chunk, len(chunks)))
                    else:
                        # Regular text
                        text = element.get('content', '')
                        
                        # Check chunk size
                        if current_chunk['text'] and len(current_chunk['text']) + len(text) > self.chunk_size:
                            chunks.append(self._finalize_chunk(current_chunk, len(chunks)))
                            current_chunk = {'text': '', 'elements': [], 'page_start': None, 'page_end': None}
                        
                        # Add to current chunk
                        current_chunk['text'] += text + ' '
                        current_chunk['elements'].append(element)
                        
                        if current_chunk['page_start'] is None:
                            current_chunk['page_start'] = page_num
                        current_chunk['page_end'] = page_num
        
        # Don't forget last chunk
        if current_chunk['text']:
            chunks.append(self._finalize_chunk(current_chunk, len(chunks)))
        
        logger.info(f"Created {len(chunks)} chunks from {len(batches)} batches")
        return chunks
    
    def _finalize_chunk(self, chunk: Dict, index: int) -> Dict:
        """Finalize a chunk for storage"""
        return {
            'chunk_id': index,
            'text': chunk['text'].strip(),
            'type': chunk.get('type', 'text'),
            'page_start': chunk.get('page_start', 0),
            'page_end': chunk.get('page_end', 0),
            'element_count': len(chunk.get('elements', [])),
            'metadata': chunk.get('metadata', {})
        }
    
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
        
        logger.info("Chunking worker started")
        
        try:
            while True:
                # Get job_id from queue
                result = await self.redis_client.blpop("prismy:chunk", timeout=5)
                
                if result:
                    _, job_id_bytes = result
                    job_id = job_id_bytes.decode('utf-8')
                    
                    try:
                        # Get full job data
                        job_data = await self.get_job_data(job_id)
                        await self.process_chunking_job(job_data)
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
    
    worker = ChunkingWorker()
    asyncio.run(worker.run())
