"""
OCR Processor
Optical Character Recognition for images and scanned PDFs
"""
import logging
from typing import Dict, Any, List, Optional
import pytesseract
from PIL import Image
import io
import base64
import numpy as np

from ..base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class OCRProcessor(BaseExtractor):
    """
    OCR processing for images and scanned PDFs
    Supports multiple languages including Vietnamese
    """
    
    VERSION = "1.0.0"
    CAPABILITIES = ["ocr_extraction", "multi_language", "image_preprocessing"]
    
    def validate_config(self):
        """Validate configuration"""
        defaults = {
            "languages": ["eng", "vie"],  # English and Vietnamese
            "confidence_threshold": 60,    # Minimum confidence
            "preprocess": True,           # Image preprocessing
            "dpi": 300,                   # DPI for conversion
            "psm": 3,                     # Page segmentation mode
            "oem": 3                      # OCR Engine mode
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                
    async def extract(self, image_data: Any, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract text from image using OCR
        
        Args:
            image_data: Image data (bytes, path, or PIL Image)
            context: Additional context (page number, etc.)
        """
        try:
            # Load image
            image = self._load_image(image_data)
            
            if self.config["preprocess"]:
                image = self._preprocess_image(image)
                
            # Configure tesseract
            custom_config = f'--oem {self.config["oem"]} --psm {self.config["psm"]}'
            
            # Extract text with confidence scores
            languages = '+'.join(self.config["languages"])
            
            # Get detailed data
            data = pytesseract.image_to_data(
                image, 
                lang=languages,
                config=custom_config,
                output_type=pytesseract.Output.DICT
            )
            
            # Extract text
            full_text = pytesseract.image_to_string(
                image,
                lang=languages,
                config=custom_config
            )
            
            # Process results
            words = []
            confidences = []
            
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:  # Valid text
                    words.append({
                        'text': data['text'][i],
                        'confidence': data['conf'][i],
                        'bbox': {
                            'x': data['left'][i],
                            'y': data['top'][i],
                            'width': data['width'][i],
                            'height': data['height'][i]
                        }
                    })
                    confidences.append(data['conf'][i])
                    
            # Calculate average confidence
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Filter by confidence
            high_confidence_words = [
                w for w in words 
                if w['confidence'] >= self.config["confidence_threshold"]
            ]
            
            return {
                "text": full_text.strip(),
                "words": high_confidence_words,
                "metadata": {
                    "languages": self.config["languages"],
                    "average_confidence": avg_confidence,
                    "total_words": len(words),
                    "high_confidence_words": len(high_confidence_words),
                    "preprocessing_applied": self.config["preprocess"]
                }
            }
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {
                "text": "",
                "words": [],
                "metadata": {"error": str(e)}
            }
            
    def _load_image(self, image_data: Any) -> Image.Image:
        """Load image from various sources"""
        if isinstance(image_data, str):
            if image_data.startswith('data:image'):
                # Base64 data URL
                base64_data = image_data.split(',')[1]
                image_bytes = base64.b64decode(base64_data)
                return Image.open(io.BytesIO(image_bytes))
            else:
                # File path
                return Image.open(image_data)
        elif isinstance(image_data, bytes):
            return Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, Image.Image):
            return image_data
        else:
            raise ValueError(f"Unsupported image data type: {type(image_data)}")
            
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image for better OCR results"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
            
        # Convert to numpy array
        img_array = np.array(image)
        
        # Apply thresholding
        threshold = 127
        img_array = ((img_array > threshold) * 255).astype(np.uint8)
        
        # Denoise (simple median filter)
        from scipy.ndimage import median_filter
        img_array = median_filter(img_array, size=2)
        
        # Convert back to PIL Image
        return Image.fromarray(img_array)
        
    def can_process(self, context: Dict[str, Any]) -> bool:
        """Check if OCR is needed"""
        # Always can process images
        return True
        
    def get_dependencies(self) -> List[str]:
        """Get required dependencies"""
        return ["pytesseract", "Pillow", "numpy", "scipy"]
        
    async def process_scanned_pdf(self, pdf_path: str) -> Dict[str, Any]:
        """Process scanned PDF by converting pages to images"""
        from pdf2image import convert_from_path
        
        results = {
            "pages": [],
            "full_text": "",
            "metadata": {
                "total_pages": 0,
                "languages": self.config["languages"]
            }
        }
        
        # Convert PDF pages to images
        images = convert_from_path(pdf_path, dpi=self.config["dpi"])
        results["metadata"]["total_pages"] = len(images)
        
        # Process each page
        for page_num, image in enumerate(images):
            logger.info(f"Processing page {page_num + 1}/{len(images)} with OCR")
            
            page_result = await self.extract(image, {"page": page_num + 1})
            
            results["pages"].append({
                "page": page_num + 1,
                "text": page_result["text"],
                "confidence": page_result["metadata"]["average_confidence"]
            })
            
            results["full_text"] += page_result["text"] + "\n\n"
            
        return results
