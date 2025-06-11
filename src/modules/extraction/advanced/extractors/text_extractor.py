"""
Text Extractor with Layout Preservation
Extracts text while maintaining document structure
"""
import logging
from typing import Dict, Any, List, Optional
import re

from ..base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class TextExtractor(BaseExtractor):
    """
    Extract text with layout and structure preservation
    """
    
    VERSION = "1.0.0"
    CAPABILITIES = ["text_extraction", "layout_preservation", "paragraph_detection"]
    
    def validate_config(self):
        """Validate configuration"""
        defaults = {
            "preserve_layout": True,
            "detect_paragraphs": True,
            "preserve_formatting": True,
            "line_overlap_threshold": 5,
            "paragraph_gap_threshold": 15,
            "extract_method": "pdfplumber"  # or "pymupdf"
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                
    async def extract(self, pdf_path: str, document_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract text from PDF with layout preservation
        """
        try:
            logger.info(f"Starting text extraction from {pdf_path}")
            
            if self.config["extract_method"] == "pdfplumber":
                result = await self._extract_with_pdfplumber(pdf_path, document_structure)
            else:
                result = await self._extract_with_pymupdf(pdf_path, document_structure)
                
            # Post-process text
            if self.config["detect_paragraphs"]:
                result["text"] = self._detect_paragraphs(result["text"])
                
            return result
            
        except Exception as e:
            logger.error(f"Text extraction failed: {e}")
            return {
                "text": "",
                "metadata": {"error": str(e)}
            }
            
    async def _extract_with_pdfplumber(self, pdf_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text using pdfplumber with layout preservation"""
        import pdfplumber
        
        full_text = ""
        pages_text = []
        layout_info = []
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                page_struct = structure["pages"][page_num] if page_num < len(structure.get("pages", [])) else {}
                
                if self.config["preserve_layout"]:
                    # Extract with layout
                    page_text = self._extract_page_with_layout(page, page_struct)
                else:
                    # Simple extraction
                    page_text = page.extract_text() or ""
                    
                pages_text.append(page_text)
                full_text += page_text + "\n\n"
                
                # Extract layout information
                if page.chars:
                    layout_info.append({
                        "page": page_num + 1,
                        "lines": self._extract_lines(page.chars),
                        "fonts": self._extract_fonts(page.chars)
                    })
                    
        return {
            "text": full_text.strip(),
            "pages": pages_text,
            "layout": layout_info,
            "metadata": {
                "extraction_method": "pdfplumber",
                "layout_preserved": self.config["preserve_layout"],
                "page_count": len(pages_text)
            }
        }
        
    def _extract_page_with_layout(self, page, page_structure: Dict[str, Any]) -> str:
        """Extract page text preserving layout"""
        if not page.chars:
            return page.extract_text() or ""
            
        # Group characters into lines
        lines = self._group_chars_into_lines(page.chars)
        
        # Sort lines by vertical position
        lines.sort(key=lambda x: x["top"])
        
        # Check for multi-column layout
        if page_structure.get("layout") == "multi_column":
            lines = self._handle_multi_column(lines)
            
        # Build text with proper spacing
        text = ""
        prev_line = None
        
        for line in lines:
            if prev_line:
                # Calculate gap between lines
                gap = line["top"] - prev_line["bottom"]
                
                if gap > self.config["paragraph_gap_threshold"]:
                    # Paragraph break
                    text += "\n\n"
                else:
                    # Normal line break
                    text += "\n"
                    
            text += line["text"]
            prev_line = line
            
        return text
        
    def _group_chars_into_lines(self, chars: List[Dict]) -> List[Dict]:
        """Group characters into lines based on vertical position"""
        if not chars:
            return []
            
        lines = []
        current_line = {
            "top": chars[0]["top"],
            "bottom": chars[0]["bottom"],
            "left": chars[0]["x0"],
            "right": chars[0]["x1"],
            "text": chars[0].get("text", ""),
            "chars": [chars[0]]
        }
        
        for char in chars[1:]:
            # Check if same line (vertical overlap)
            if abs(char["top"] - current_line["top"]) < self.config["line_overlap_threshold"]:
                # Add to current line
                current_line["text"] += char.get("text", "")
                current_line["right"] = max(current_line["right"], char["x1"])
                current_line["bottom"] = max(current_line["bottom"], char["bottom"])
                current_line["chars"].append(char)
            else:
                # Start new line
                lines.append(current_line)
                current_line = {
                    "top": char["top"],
                    "bottom": char["bottom"],
                    "left": char["x0"],
                    "right": char["x1"],
                    "text": char.get("text", ""),
                    "chars": [char]
                }
                
        lines.append(current_line)
        
        # Sort characters within each line by x position
        for line in lines:
            line["chars"].sort(key=lambda x: x["x0"])
            line["text"] = "".join(c.get("text", "") for c in line["chars"])
            
        return lines
        
    def _handle_multi_column(self, lines: List[Dict]) -> List[Dict]:
        """Handle multi-column layout"""
        # Group lines by column (x-position clustering)
        columns = {}
        
        for line in lines:
            col_key = round(line["left"] / 50) * 50  # Cluster by 50pt intervals
            if col_key not in columns:
                columns[col_key] = []
            columns[col_key].append(line)
            
        # Sort columns left to right
        sorted_columns = sorted(columns.items(), key=lambda x: x[0])
        
        # Rebuild lines reading left-to-right, top-to-bottom
        result = []
        max_height = max(line["bottom"] for line in lines)
        
        # Process in horizontal bands
        band_height = 100  # Points
        for band_start in range(0, int(max_height), band_height):
            band_end = band_start + band_height
            
            # Get lines in this band from each column
            for col_key, col_lines in sorted_columns:
                band_lines = [l for l in col_lines 
                            if band_start <= l["top"] < band_end]
                result.extend(sorted(band_lines, key=lambda x: x["top"]))
                
        return result
        
    def _detect_paragraphs(self, text: str) -> str:
        """Detect and format paragraphs"""
        # Split into lines
        lines = text.split('\n')
        
        # Detect paragraph boundaries
        paragraphs = []
        current_para = []
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            if not line:
                # Empty line - paragraph break
                if current_para:
                    paragraphs.append(' '.join(current_para))
                    current_para = []
            else:
                # Check if line is a heading (simple heuristic)
                if (len(line) < 100 and 
                    (line.isupper() or 
                     re.match(r'^(Chapter|Section|\d+\.|\d+\))', line))):
                    # Likely a heading
                    if current_para:
                        paragraphs.append(' '.join(current_para))
                        current_para = []
                    paragraphs.append(line)
                else:
                    current_para.append(line)
                    
        if current_para:
            paragraphs.append(' '.join(current_para))
            
        return '\n\n'.join(paragraphs)
        
    def _extract_lines(self, chars: List[Dict]) -> List[Dict]:
        """Extract line information"""
        lines = self._group_chars_into_lines(chars)
        return [
            {
                "text": line["text"],
                "bbox": [line["left"], line["top"], line["right"], line["bottom"]]
            }
            for line in lines
        ]
        
    def _extract_fonts(self, chars: List[Dict]) -> Dict[str, int]:
        """Extract font usage statistics"""
        fonts = {}
        for char in chars:
            font = char.get("fontname", "unknown")
            fonts[font] = fonts.get(font, 0) + 1
        return fonts
        
    async def _extract_with_pymupdf(self, pdf_path: str, structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract text using PyMuPDF"""
        import fitz
        
        doc = fitz.open(pdf_path)
        full_text = ""
        pages_text = []
        
        for page in doc:
            page_text = page.get_text()
            pages_text.append(page_text)
            full_text += page_text + "\n\n"
            
        doc.close()
        
        return {
            "text": full_text.strip(),
            "pages": pages_text,
            "metadata": {
                "extraction_method": "pymupdf",
                "page_count": len(pages_text)
            }
        }
        
    def can_process(self, document_structure: Dict[str, Any]) -> bool:
        """Text extraction is always possible"""
        return True
        
    def get_dependencies(self) -> List[str]:
        """Get required dependencies"""
        return ["pdfplumber", "PyMuPDF"]
