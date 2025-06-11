"""
Streaming PDF Extractor for 500+ pages documents
Enhanced version of AdvancedPDFProcessor with streaming and batching
"""
import logging
import asyncio
import json
from typing import Dict, Any, AsyncIterator, Optional, List
from pathlib import Path
import tempfile
import os
import gc
from datetime import datetime

import pdfplumber
import pymupdf
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer, LTFigure, LTImage

from ..advanced.core_with_ocr_formula import AdvancedPDFProcessor
from ..advanced.processors import OCRProcessor, FormulaProcessor
from ..advanced.extractors import TableExtractor

logger = logging.getLogger(__name__)

class StreamingPDFExtractor(AdvancedPDFProcessor):
    """
    Enhanced PDF Extractor with streaming support for 500+ pages
    """
    
    VERSION = "2.0.0"
    BATCH_SIZE = 50
    MAX_MEMORY_MB = 500
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with streaming configuration"""
        streaming_config = {
            "batch_size": self.BATCH_SIZE,
            "enable_streaming": True,
            "output_format": "jsonl",
            "temp_dir": tempfile.gettempdir(),
            "memory_limit_mb": self.MAX_MEMORY_MB,
            **(config or {})
        }
        super().__init__(streaming_config)
        
        self.batch_size = streaming_config["batch_size"]
        self.temp_dir = Path(streaming_config["temp_dir"])
        self.memory_limit = streaming_config["memory_limit_mb"]
        
        self._current_batch = []
        self._batch_count = 0
        self._total_pages = 0
        
    async def process_streaming(self, pdf_path: str) -> AsyncIterator[Dict[str, Any]]:
        """
        Process PDF in streaming mode, yielding batches
        
        Args:
            pdf_path: Path to PDF file
            
        Yields:
            Dict containing batch data
        """
        pdf_path = Path(pdf_path)
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
        logger.info(f"Starting streaming extraction: {pdf_path}")
        
        with pdfplumber.open(pdf_path) as pdf:
            self._total_pages = len(pdf.pages)
            
        logger.info(f"Total pages: {self._total_pages}")
        
        output_file = self.temp_dir / f"extraction_{pdf_path.stem}_{datetime.now():%Y%m%d_%H%M%S}.jsonl"
        
        try:
            async for batch in self._extract_batches(pdf_path):
                with open(output_file, 'a', encoding='utf-8') as f:
                    json.dump(batch, f, ensure_ascii=False)
                    f.write('\n')
                    
                yield {
                    "batch_id": batch["batch_id"],
                    "pages": batch["pages"],
                    "progress": batch["progress"],
                    "data": batch
                }
                
                gc.collect()
                
            yield {
                "status": "completed",
                "output_file": str(output_file),
                "total_pages": self._total_pages,
                "total_batches": self._batch_count
            }
            
        except Exception as e:
            logger.error(f"Streaming extraction failed: {e}")
            yield {
                "status": "error",
                "error": str(e),
                "partial_output": str(output_file) if output_file.exists() else None
            }
            
    async def _extract_batches(self, pdf_path: Path) -> AsyncIterator[Dict[str, Any]]:
        """Extract PDF in batches"""
        with pdfplumber.open(pdf_path) as pdf:
            for batch_start in range(0, self._total_pages, self.batch_size):
                batch_end = min(batch_start + self.batch_size, self._total_pages)
                self._batch_count += 1
                
                logger.info(f"Processing batch {self._batch_count}: pages {batch_start+1}-{batch_end}")
                
                batch_data = {
                    "batch_id": self._batch_count,
                    "pages": f"{batch_start+1}-{batch_end}",
                    "progress": (batch_end / self._total_pages) * 100,
                    "timestamp": datetime.now().isoformat(),
                    "content": []
                }
                
                for page_num in range(batch_start, batch_end):
                    page = pdf.pages[page_num]
                    page_data = await self._process_page(page, page_num + 1, pdf_path)
                    batch_data["content"].append(page_data)
                    
                yield batch_data
                
    async def _process_page(self, page, page_num: int, pdf_path: Path) -> Dict[str, Any]:
        """Process a single page"""
        page_data = {
            "page": page_num,
            "elements": []
        }
        
        try:
            text = page.extract_text()
            if text and len(text.strip()) > 10:
                words = page.extract_words()
                if words:
                    page_data["elements"].append({
                        "type": "text",
                        "content": text,
                        "word_count": len(words),
                        "bbox": self._get_text_bbox(words)
                    })
        except Exception as e:
            logger.warning(f"Text extraction failed for page {page_num}: {e}")
            
        if self.config.get("extract_tables", True):
            try:
                tables = page.extract_tables()
                for idx, table in enumerate(tables):
                    if table:
                        page_data["elements"].append({
                            "type": "table",
                            "table_id": f"t_{page_num}_{idx}",
                            "rows": len(table),
                            "cols": len(table[0]) if table else 0,
                            "data": table
                        })
            except Exception as e:
                logger.warning(f"Table extraction failed for page {page_num}: {e}")
                
        if self.config.get("enable_ocr", True):
            if not text or len(text.strip()) < 50:
                page_data["elements"].append({
                    "type": "possible_scan",
                    "requires_ocr": True,
                    "page": page_num
                })
                
        if self.config.get("extract_formulas", True):
            formula_indicators = ['∫', '∑', '∏', '√', '∞', '∂', '∇', '∈']
            if text and any(indicator in text for indicator in formula_indicators):
                page_data["elements"].append({
                    "type": "formula_detected",
                    "page": page_num,
                    "indicators_found": [ind for ind in formula_indicators if ind in text]
                })
                
        return page_data
        
    def _get_text_bbox(self, words: List[Dict]) -> List[float]:
        """Get bounding box from word list"""
        if not words:
            return [0, 0, 0, 0]
            
        x0 = min(w['x0'] for w in words)
        y0 = min(w['top'] for w in words)
        x1 = max(w['x1'] for w in words)
        y1 = max(w['bottom'] for w in words)
        
        return [x0, y0, x1, y1]
        
    async def extract_with_ocr_batch(self, pdf_path: str, batch_pages: List[int]) -> Dict[str, Any]:
        """
        Extract specific pages with OCR (for scanned pages)
        
        Args:
            pdf_path: Path to PDF
            batch_pages: List of page numbers to OCR
        """
        logger.info(f"Running OCR on pages: {batch_pages}")
        
        ocr_results = []
        
        import pdf2image
        
        for page_num in batch_pages:
            try:
                images = pdf2image.convert_from_path(
                    pdf_path,
                    first_page=page_num,
                    last_page=page_num,
                    dpi=300
                )
                
                if images:
                    import pytesseract
                    text = pytesseract.image_to_string(
                        images[0],
                        lang='eng+vie'
                    )
                    
                    ocr_results.append({
                        "page": page_num,
                        "text": text,
                        "method": "tesseract"
                    })
                    
            except Exception as e:
                logger.error(f"OCR failed for page {page_num}: {e}")
                
        return {"ocr_results": ocr_results}
        
    def estimate_processing_time(self, total_pages: int) -> Dict[str, float]:
        """Estimate processing time for document"""
        time_per_page = {
            "text_only": 0.1,
            "with_tables": 0.5,
            "with_ocr": 2.0,
            "with_formulas": 0.3
        }
        
        avg_time = sum(time_per_page.values()) / len(time_per_page)
        total_seconds = total_pages * avg_time
        
        return {
            "estimated_seconds": total_seconds,
            "estimated_minutes": total_seconds / 60,
            "confidence": "medium",
            "factors": time_per_page
        }


class BatchProcessor:
    """
    Process extraction results in batches for translation
    """
    
    def __init__(self, extractor: StreamingPDFExtractor):
        self.extractor = extractor
        self.batch_queue = asyncio.Queue()
        
    async def process_pdf_for_translation(
        self, 
        pdf_path: str,
        callback=None
    ) -> str:
        """
        Process PDF and prepare for translation
        
        Args:
            pdf_path: Path to PDF
            callback: Progress callback function
            
        Returns:
            Path to JSONL file ready for translation
        """
        output_files = []
        
        async for batch in self.extractor.process_streaming(pdf_path):
            if batch.get("status") == "completed":
                return batch["output_file"]
                
            if callback:
                await callback(batch)
                
            if "data" in batch:
                text_content = self._extract_translatable_text(batch["data"])
                if text_content:
                    await self.batch_queue.put({
                        "batch_id": batch["batch_id"],
                        "text": text_content,
                        "metadata": batch["data"]
                    })
                    
    def _extract_translatable_text(self, batch_data: Dict) -> str:
        """Extract only translatable text from batch"""
        texts = []
        
        for page in batch_data.get("content", []):
            for element in page.get("elements", []):
                if element["type"] == "text":
                    texts.append(element["content"])
                elif element["type"] == "table":
                    table_text = self._table_to_text(element["data"])
                    texts.append(table_text)
                    
        return "\n\n".join(texts)
        
    def _table_to_text(self, table_data: List[List[str]]) -> str:
        """Convert table to readable text"""
        lines = []
        for row in table_data:
            if row:
                lines.append(" | ".join(str(cell) for cell in row))
        return "\n".join(lines)