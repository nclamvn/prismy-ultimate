# src/modules/extraction/enhanced_extractor.py
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import asyncio

from .table.table_extractor import get_table_extractor
from .v2.streaming_extractor import StreamingPDFExtractor

logger = logging.getLogger(__name__)

class EnhancedPDFExtractor(StreamingPDFExtractor):
    """Enhanced PDF extractor with table preservation"""
    
    def __init__(self, use_ocr: bool = False):
        super().__init__(use_ocr)
        self.table_extractor = get_table_extractor()
        
    async def extract_with_tables(
        self,
        pdf_path: str,
        batch_size: int = 5
    ) -> Dict[str, Any]:
        """Extract PDF content with table detection and preservation"""
        
        # First, extract tables from all pages
        logger.info(f"Extracting tables from {pdf_path}")
        tables_by_page = await asyncio.to_thread(
            self.table_extractor.extract_all_tables,
            pdf_path
        )
        
        # Log table detection results
        total_tables = sum(len(tables) for tables in tables_by_page.values())
        logger.info(f"Found {total_tables} tables across {len(tables_by_page)} pages")
        
        # Extract regular content
        async for batch in self.extract_streaming(pdf_path, batch_size):
            # Enhance batch with table information
            enhanced_batch = batch.copy()
            
            # Add table data to relevant pages
            for element in enhanced_batch.get('elements', []):
                page_num = element.get('page_num', 0)
                
                # Check if this page has tables
                if page_num in tables_by_page:
                    element['tables'] = tables_by_page[page_num]
                    element['has_tables'] = True
                else:
                    element['tables'] = []
                    element['has_tables'] = False
            
            # Add table summary to batch metadata
            enhanced_batch['table_count'] = total_tables
            enhanced_batch['pages_with_tables'] = list(tables_by_page.keys())
            
            yield enhanced_batch
    
    def format_element_with_tables(self, element: Dict[str, Any]) -> str:
        """Format element content including tables"""
        formatted_parts = []
        
        # Add regular text content
        if element.get('text'):
            formatted_parts.append(element['text'])
        
        # Add tables
        for table in element.get('tables', []):
            if not table.get('is_empty', True):
                table_formatted = self.table_extractor.format_table_for_translation(table)
                formatted_parts.append(table_formatted)
        
        return '\n\n'.join(formatted_parts)
    
    def extract_tables_only(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract only tables from PDF"""
        tables_by_page = self.table_extractor.extract_all_tables(pdf_path)
        
        # Flatten to list
        all_tables = []
        for page_num, tables in tables_by_page.items():
            for table in tables:
                table['source_pdf'] = pdf_path
                all_tables.append(table)
        
        return all_tables
