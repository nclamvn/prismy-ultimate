import fitz  # PyMuPDF
import cv2
import numpy as np
from PIL import Image
import pytesseract
import re
from typing import List, Dict, Tuple

class AdvancedPDFProcessor:
    def __init__(self):
        self.math_patterns = [
            r'\$[^$]+\$',  # Inline math
            r'\$\$[^$]+\$\$',  # Display math
            r'\\begin\{equation\}.*?\\end\{equation\}',
            r'\\begin\{align\}.*?\\end\{align\}'
        ]
    
    def extract_with_ocr(self, pdf_path: str) -> List[Dict]:
        """Extract text with OCR support for scanned PDFs"""
        doc = fitz.open(pdf_path)
        pages_data = []
        
        for page_num, page in enumerate(doc):
            # Try text extraction first
            text = page.get_text()
            
            # If no text (scanned PDF), use OCR
            if len(text.strip()) < 10:
                # Convert page to image
                pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))  # 2x zoom for better OCR
                img_data = pix.tobytes("png")
                img = Image.open(io.BytesIO(img_data))
                
                # OCR with Vietnamese support
                text = pytesseract.image_to_string(img, lang='vie+eng')
            
            # Extract images that might contain formulas
            image_list = page.get_images()
            formulas = []
            
            for img_index, img in enumerate(image_list):
                # Extract image
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha < 4:  # GRAY or RGB
                    img_data = pix.tobytes("png")
                    # Check if image contains formula
                    if self.is_formula_image(img_data):
                        formula_text = self.extract_formula(img_data)
                        formulas.append(formula_text)
                pix = None
            
            pages_data.append({
                'page_num': page_num,
                'text': text,
                'formulas': formulas,
                'has_ocr': len(text.strip()) < 10
            })
        
        doc.close()
        return pages_data
    
    def is_formula_image(self, img_data: bytes) -> bool:
        """Detect if image likely contains mathematical formula"""
        img = cv2.imdecode(np.frombuffer(img_data, np.uint8), cv2.IMREAD_GRAYSCALE)
        
        # Check for mathematical symbols using contour analysis
        _, binary = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Heuristic: formulas have specific aspect ratios and symbol density
        if len(contours) > 5:  # Multiple symbols
            return True
        return False
    
    def extract_formula(self, img_data: bytes) -> str:
        """Extract formula from image using OCR or ML model"""
        # For now, simple OCR - later can integrate pix2tex or Mathpix API
        img = Image.open(io.BytesIO(img_data))
        
        # Preprocess for better formula OCR
        img = img.convert('L')  # Grayscale
        img = img.point(lambda x: 0 if x < 128 else 255, '1')  # Binary
        
        # OCR with math symbols
        formula_text = pytesseract.image_to_string(img, config='--psm 7')
        
        # Clean up common OCR errors in formulas
        formula_text = formula_text.replace('×', '*')
        formula_text = formula_text.replace('÷', '/')
        
        return formula_text
    
    def extract_tables(self, pdf_path: str) -> List[Dict]:
        """Extract tables from PDF"""
        import camelot
        
        tables = camelot.read_pdf(pdf_path, pages='all', flavor='stream')
        
        extracted_tables = []
        for table in tables:
            extracted_tables.append({
                'page': table.page,
                'data': table.df.to_dict('records'),
                'accuracy': table.accuracy
            })
        
        return extracted_tables

# Update main processor to use advanced extraction
def extract_pdf_advanced(file_path: str, options: Dict) -> List[Dict]:
    processor = AdvancedPDFProcessor()
    
    # Extract with OCR and formula detection
    pages_data = processor.extract_with_ocr(file_path)
    
    # Extract tables if needed
    if options.get('extract_tables', True):
        tables = processor.extract_tables(file_path)
        
        # Merge table data with pages
        for table in tables:
            page_idx = table['page'] - 1
            if page_idx < len(pages_data):
                pages_data[page_idx]['tables'] = pages_data[page_idx].get('tables', [])
                pages_data[page_idx]['tables'].append(table['data'])
    
    return pages_data
