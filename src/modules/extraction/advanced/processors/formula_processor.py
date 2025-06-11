"""
Formula Processor
Extract and process mathematical formulas from PDFs
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
import re
from PIL import Image
import io

from ..base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class FormulaProcessor(BaseExtractor):
    """
    Extract mathematical formulas and equations
    Convert to LaTeX format when possible
    """
    
    VERSION = "1.0.0"
    CAPABILITIES = ["formula_detection", "latex_conversion", "equation_parsing"]
    
    def validate_config(self):
        """Validate configuration"""
        defaults = {
            "detect_inline": True,      # Detect inline formulas
            "detect_display": True,     # Detect display formulas
            "convert_to_latex": True,   # Convert to LaTeX
            "extract_images": True,     # Extract formula images
            "confidence_threshold": 0.7
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                
    async def extract(self, pdf_path: str, document_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract formulas from PDF
        """
        try:
            logger.info(f"Starting formula extraction from {pdf_path}")
            
            formulas = []
            errors = []
            
            # Method 1: Pattern-based detection
            text_formulas = await self._extract_text_formulas(pdf_path)
            formulas.extend(text_formulas)
            
            # Method 2: Image-based detection (for rendered formulas)
            if self.config["extract_images"]:
                image_formulas = await self._extract_image_formulas(pdf_path, document_structure)
                formulas.extend(image_formulas)
            
            # Deduplicate and process
            formulas = self._process_formulas(formulas)
            
            return {
                "formulas": formulas,
                "metadata": {
                    "total_formulas": len(formulas),
                    "inline_count": len([f for f in formulas if f["type"] == "inline"]),
                    "display_count": len([f for f in formulas if f["type"] == "display"]),
                    "extraction_methods": ["pattern", "image"] if self.config["extract_images"] else ["pattern"]
                }
            }
            
        except Exception as e:
            logger.error(f"Formula extraction failed: {e}")
            return {
                "formulas": [],
                "metadata": {"error": str(e)}
            }
            
    async def _extract_text_formulas(self, pdf_path: str) -> List[Dict[str, Any]]:
        """Extract formulas using pattern matching"""
        import pdfplumber
        
        formulas = []
        
        # Common formula patterns
        patterns = {
            'inline_math': r'\$([^\$]+)\$',                    # $formula$
            'display_math': r'\$\$([^\$]+)\$\$',              # $$formula$$
            'latex_inline': r'\\[(][^)]+\\[)]',               # \(formula\)
            'latex_display': r'\\[\[]([^\]]+)\\[\]]',         # \[formula\]
            'equation': r'([a-zA-Z]+\s*=\s*[^.;,\n]+)',      # x = formula
            'function': r'([a-zA-Z]+\([^)]+\)\s*=\s*[^.;,\n]+)',  # f(x) = formula
            'integral': r'(∫[^.;,\n]+)',                      # Integral
            'sum': r'(∑[^.;,\n]+)',                          # Summation
            'fraction': r'(\\frac\{[^}]+\}\{[^}]+\})',       # LaTeX fraction
        }
        
        with pdfplumber.open(pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                
                # Search for formulas
                for pattern_name, pattern in patterns.items():
                    matches = re.finditer(pattern, text)
                    
                    for match in matches:
                        formula_text = match.group(1) if match.groups() else match.group(0)
                        
                        # Determine formula type
                        formula_type = "display" if "display" in pattern_name else "inline"
                        
                        formulas.append({
                            "text": formula_text,
                            "type": formula_type,
                            "page": page_num + 1,
                            "pattern": pattern_name,
                            "latex": self._convert_to_latex(formula_text) if self.config["convert_to_latex"] else None,
                            "position": match.span()
                        })
                        
        return formulas
        
    async def _extract_image_formulas(self, pdf_path: str, structure: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract formulas from images (for complex rendered formulas)"""
        formulas = []
        
        # This would use specialized formula detection
        # For now, we'll do basic detection
        import fitz  # PyMuPDF
        
        doc = fitz.open(pdf_path)
        
        for page_num, page in enumerate(doc):
            # Look for images that might be formulas
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                try:
                    # Extract image
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        # Check if image might be a formula
                        if self._is_likely_formula_image(base_image):
                            formulas.append({
                                "type": "image",
                                "page": page_num + 1,
                                "image_data": base_image["image"],
                                "bbox": img_info[1:5] if len(img_info) > 4 else None,
                                "latex": None  # Would need specialized OCR
                            })
                except Exception as e:
                    logger.warning(f"Failed to process image {img_index}: {e}")
                    
        doc.close()
        return formulas
        
    def _is_likely_formula_image(self, image_data: Dict) -> bool:
        """Heuristic to check if image might be a formula"""
        # Check aspect ratio and size
        width = image_data.get("width", 0)
        height = image_data.get("height", 0)
        
        if width == 0 or height == 0:
            return False
            
        aspect_ratio = width / height
        
        # Formulas often have specific aspect ratios
        # and are typically small to medium sized
        if 0.5 < aspect_ratio < 10 and 50 < width < 1000 and 20 < height < 500:
            return True
            
        return False
        
    def _convert_to_latex(self, formula_text: str) -> str:
        """Convert formula text to LaTeX format"""
        # Basic conversions
        conversions = {
            '×': r'\times',
            '÷': r'\div',
            '≤': r'\leq',
            '≥': r'\geq',
            '≠': r'\neq',
            '≈': r'\approx',
            '∞': r'\infty',
            'α': r'\alpha',
            'β': r'\beta',
            'γ': r'\gamma',
            'δ': r'\delta',
            'θ': r'\theta',
            'π': r'\pi',
            'σ': r'\sigma',
            '∑': r'\sum',
            '∫': r'\int',
            '√': r'\sqrt',
            '^2': r'^{2}',
            '^3': r'^{3}',
            '_1': r'_{1}',
            '_2': r'_{2}',
        }
        
        latex = formula_text
        for symbol, latex_symbol in conversions.items():
            latex = latex.replace(symbol, latex_symbol)
            
        # Handle fractions (simple pattern)
        latex = re.sub(r'(\d+)/(\d+)', r'\\frac{\1}{\2}', latex)
        
        # Handle superscripts
        latex = re.sub(r'\^(\w+)', r'^{\1}', latex)
        
        # Handle subscripts
        latex = re.sub(r'_(\w+)', r'_{\1}', latex)
        
        return latex
        
    def _process_formulas(self, formulas: List[Dict]) -> List[Dict]:
        """Process and deduplicate formulas"""
        # Remove duplicates based on text
        seen = set()
        unique_formulas = []
        
        for formula in formulas:
            formula_key = f"{formula.get('text', '')}_{formula.get('page', 0)}"
            
            if formula_key not in seen:
                seen.add(formula_key)
                
                # Add ID
                formula["id"] = f"formula_{len(unique_formulas)}"
                
                # Classify formula
                formula["category"] = self._classify_formula(formula.get("text", ""))
                
                unique_formulas.append(formula)
                
        return unique_formulas
        
    def _classify_formula(self, formula_text: str) -> str:
        """Classify formula type"""
        if "=" in formula_text:
            if "f(" in formula_text or re.match(r'[a-zA-Z]+\(', formula_text):
                return "function"
            else:
                return "equation"
        elif "∫" in formula_text or "int" in formula_text:
            return "integral"
        elif "∑" in formula_text or "sum" in formula_text:
            return "summation"
        elif "lim" in formula_text:
            return "limit"
        elif any(op in formula_text for op in ["+", "-", "*", "/", "×", "÷"]):
            return "arithmetic"
        else:
            return "other"
            
    def can_process(self, document_structure: Dict[str, Any]) -> bool:
        """Check if document might contain formulas"""
        # Could check for keywords like "equation", "formula", etc.
        return True
        
    def get_dependencies(self) -> List[str]:
        """Get required dependencies"""
        return ["pdfplumber", "PyMuPDF", "pillow"]
