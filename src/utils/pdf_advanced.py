import fitz  # PyMuPDF
from PIL import Image
import io
import re
from typing import List, Dict

class AdvancedPDFExtractor:
    def __init__(self):
        self.use_ocr = True
        
    def extract_page_content(self, page: fitz.Page, page_num: int) -> Dict:
        """Extract all content from a page"""
        result = {
            'page_num': page_num,
            'text': '',
            'images': [],
            'is_scanned': False
        }
        
        # Try normal text extraction first
        text = page.get_text()
        
        # If text is too short, likely a scanned page
        if len(text.strip()) < 50 and self.use_ocr:
            result['is_scanned'] = True
            # Use PyMuPDF's built-in text extraction with OCR hint
            text = page.get_text("text", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_PRESERVE_WHITESPACE)
            
            # If still no text, try extracting as image text
            if len(text.strip()) < 10:
                # Get text blocks
                blocks = page.get_text("dict")
                text = self._extract_text_from_blocks(blocks)
            
        result['text'] = text
        
        # Extract images
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(page.parent, xref)
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    result['images'].append({
                        'index': img_index,
                        'data': img_data,
                        'bbox': img[1:5] if len(img) > 4 else None
                    })
                pix = None
            except:
                pass  # Skip problematic images
            
        return result
    
    def _extract_text_from_blocks(self, blocks: Dict) -> str:
        """Extract text from block dictionary"""
        text_parts = []
        for block in blocks.get("blocks", []):
            if block.get("type") == 0:  # Text block
                for line in block.get("lines", []):
                    for span in line.get("spans", []):
                        text_parts.append(span.get("text", ""))
                    text_parts.append("\n")
                text_parts.append("\n")
        return "".join(text_parts)
    
    def smart_chunk_text(self, text: str, max_chars: int = 1000) -> List[str]:
        """Smart chunking that preserves sentences and paragraphs"""
        if not text.strip():
            return [""]
            
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            # If adding this paragraph exceeds limit
            if len(current_chunk) + len(para) > max_chars:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If paragraph itself is too long, split by sentences
                if len(para) > max_chars:
                    sentences = re.split(r'(?<=[.!?])\s+', para)
                    for sent in sentences:
                        if len(current_chunk) + len(sent) > max_chars:
                            if current_chunk:
                                chunks.append(current_chunk.strip())
                            current_chunk = sent
                        else:
                            current_chunk += " " + sent
                else:
                    current_chunk = para
            else:
                current_chunk += "\n\n" + para if current_chunk else para
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks if chunks else [""]
