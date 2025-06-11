"""
Simple PDF Extractor for clean architecture
"""
import PyPDF2
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class PDFExtractor:
    """Extract text from PDF files"""
    
    def extract(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            text_content = []
            
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    text_content.append(text)
                    
            return '\n'.join(text_content)
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            raise

    def extract_with_metadata(self, file_path: str) -> Dict[str, Any]:
        """Extract text with metadata"""
        text = self.extract(file_path)
        
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            
            metadata = {
                "pages": len(pdf_reader.pages),
                "text": text,
                "info": pdf_reader.metadata if hasattr(pdf_reader, 'metadata') else {}
            }
            
        return metadata
