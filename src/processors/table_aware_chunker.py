# src/processors/table_aware_chunker.py
from typing import Dict, Any, List
import logging
from ..core.base import BaseProcessor

logger = logging.getLogger(__name__)

class TableAwareChunker(BaseProcessor):
    """Smart chunking that preserves table integrity"""
    
    def __init__(self, max_chunk_size: int = 3000):
        super().__init__()
        self.max_chunk_size = max_chunk_size
        
    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process extraction data with table awareness"""
        elements = data.get("elements", [])
        
        chunks = []
        current_chunk = {
            "text": "",
            "tables": [],
            "elements": [],
            "page_range": None,
            "has_tables": False
        }
        
        for element in elements:
            # Handle tables specially
            if element.get('has_tables') and element.get('tables'):
                # Complete current chunk if it has content
                if current_chunk["text"]:
                    chunks.append(current_chunk)
                    current_chunk = self._create_new_chunk()
                
                # Create separate chunk for each table
                for table in element['tables']:
                    if not table.get('is_empty', True):
                        table_chunk = {
                            "text": f"[Table from page {element.get('page_num', 'unknown')}]",
                            "tables": [table],
                            "elements": [element],
                            "page_range": (element.get('page_num'), element.get('page_num')),
                            "has_tables": True,
                            "is_table_chunk": True,
                            "table_id": table.get('table_id')
                        }
                        chunks.append(table_chunk)
            
            # Handle regular text
            text = element.get('text', '').strip()
            if text:
                # Check if adding this text exceeds chunk size
                if len(current_chunk["text"]) + len(text) > self.max_chunk_size:
                    # Save current chunk
                    if current_chunk["text"]:
                        chunks.append(current_chunk)
                    # Start new chunk
                    current_chunk = self._create_new_chunk()
                
                # Add to current chunk
                if current_chunk["text"]:
                    current_chunk["text"] += "\n\n"
                current_chunk["text"] += text
                current_chunk["elements"].append(element)
                
                # Update page range
                page_num = element.get('page_num')
                if page_num:
                    if current_chunk["page_range"] is None:
                        current_chunk["page_range"] = (page_num, page_num)
                    else:
                        current_chunk["page_range"] = (
                            current_chunk["page_range"][0],
                            page_num
                        )
        
        # Don't forget last chunk
        if current_chunk["text"]:
            chunks.append(current_chunk)
        
        # Log chunking results
        table_chunks = sum(1 for c in chunks if c.get('is_table_chunk'))
        text_chunks = len(chunks) - table_chunks
        
        logger.info(f"Created {len(chunks)} chunks: {text_chunks} text, {table_chunks} table")
        
        return {
            "chunks": chunks,
            "metadata": {
                "total_chunks": len(chunks),
                "table_chunks": table_chunks,
                "text_chunks": text_chunks,
                "chunking_method": "table_aware"
            }
        }
    
    def _create_new_chunk(self) -> Dict[str, Any]:
        """Create a new empty chunk"""
        return {
            "text": "",
            "tables": [],
            "elements": [],
            "page_range": None,
            "has_tables": False,
            "is_table_chunk": False
        }
