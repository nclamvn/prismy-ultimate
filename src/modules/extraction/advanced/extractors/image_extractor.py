"""
Fixed Image Extractor with better error handling
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
import io
from PIL import Image
import base64

from ..base_extractor import BaseExtractor

logger = logging.getLogger(__name__)

class ImageExtractor(BaseExtractor):
    """Extract images from PDF with better error handling"""
    
    VERSION = "1.0.1"
    CAPABILITIES = ["image_extraction", "ocr_ready", "metadata_preservation"]
    
    def validate_config(self):
        """Validate configuration"""
        defaults = {
            "min_width": 50,
            "min_height": 50,
            "image_format": "PNG",
            "compress": True,
            "compression_quality": 85,
            "max_images_per_page": 50
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                
    async def extract(self, pdf_path: str, document_structure: Dict[str, Any]) -> Dict[str, Any]:
        """Extract images from PDF"""
        try:
            logger.info(f"Starting image extraction from {pdf_path}")
            
            images = []
            errors = []
            
            # Try PyMuPDF first
            try:
                extracted_images = await self._extract_with_pymupdf_fixed(pdf_path)
                logger.info(f"PyMuPDF extracted {len(extracted_images)} images")
            except Exception as e:
                logger.warning(f"PyMuPDF failed: {e}, trying pdf2image")
                # Fallback to pdf2image
                try:
                    extracted_images = await self._extract_with_pdf2image(pdf_path)
                except Exception as e2:
                    logger.error(f"Both methods failed: {e2}")
                    extracted_images = []
            
            # Process images
            for idx, img_data in enumerate(extracted_images):
                try:
                    processed_image = await self._process_image(img_data, idx)
                    if processed_image:
                        images.append(processed_image)
                except Exception as e:
                    logger.error(f"Error processing image {idx}: {e}")
                    errors.append(f"Image {idx}: {str(e)}")
                    
            return {
                "images": images,
                "metadata": {
                    "total_images": len(images),
                    "extraction_method": "PyMuPDF/pdf2image",
                    "errors": errors
                }
            }
            
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            return {"images": [], "metadata": {"error": str(e)}}
            
    async def _extract_with_pymupdf_fixed(self, pdf_path: str) -> List[Dict]:
        """Fixed PyMuPDF extraction"""
        import fitz
        
        extracted_images = []
        doc = fitz.open(pdf_path)
        
        for page_num, page in enumerate(doc):
            # Get images in page
            image_list = page.get_images(full=True)
            
            for img_index, img_info in enumerate(image_list):
                try:
                    # Extract image by xref
                    xref = img_info[0]
                    base_image = doc.extract_image(xref)
                    
                    if base_image:
                        image_bytes = base_image["image"]
                        
                        extracted_images.append({
                            "data": image_bytes,
                            "page": page_num + 1,
                            "index": img_index,
                            "ext": base_image.get("ext", "png"),
                            "width": base_image.get("width", 0),
                            "height": base_image.get("height", 0),
                            "bbox": {"x0": 0, "y0": 0, "x1": 100, "y1": 100}  # Placeholder
                        })
                except Exception as e:
                    logger.warning(f"Failed to extract image {img_index} on page {page_num}: {e}")
                    
        doc.close()
        return extracted_images
        
    async def _extract_with_pdf2image(self, pdf_path: str) -> List[Dict]:
        """Fallback extraction using pdf2image"""
        from pdf2image import convert_from_path
        
        extracted_images = []
        
        # Convert pages to images
        pages = convert_from_path(pdf_path, dpi=150)
        
        for page_num, page_img in enumerate(pages):
            # Save page as image
            img_buffer = io.BytesIO()
            page_img.save(img_buffer, format='PNG')
            img_buffer.seek(0)
            
            extracted_images.append({
                "data": img_buffer.getvalue(),
                "page": page_num + 1,
                "index": 0,
                "ext": "png",
                "width": page_img.width,
                "height": page_img.height,
                "bbox": {"x0": 0, "y0": 0, "x1": page_img.width, "y1": page_img.height}
            })
            
        return extracted_images
        
    async def _process_image(self, img_data: Dict, idx: int) -> Optional[Dict[str, Any]]:
        """Process image data"""
        try:
            # Load image
            img = Image.open(io.BytesIO(img_data["data"]))
            
            # Check size
            if img.width < self.config["min_width"] or img.height < self.config["min_height"]:
                return None
                
            # Convert if needed
            if self.config["image_format"] == "JPEG" and img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                img = rgb_img
                
            # Save to bytes
            output = io.BytesIO()
            img.save(output, format=self.config["image_format"])
            processed_data = output.getvalue()
            
            # Base64 encode
            base64_data = base64.b64encode(processed_data).decode('utf-8')
            
            return {
                "id": f"image_{idx}",
                "page": img_data["page"],
                "data": base64_data,
                "format": self.config["image_format"],
                "width": img.width,
                "height": img.height,
                "size_bytes": len(processed_data),
                "bbox": img_data.get("bbox"),
                "ocr_ready": True
            }
            
        except Exception as e:
            logger.error(f"Image processing error: {e}")
            return None
            
    def can_process(self, document_structure: Dict[str, Any]) -> bool:
        """Check if document has images"""
        return True  # Always try to extract
        
    def get_dependencies(self) -> List[str]:
        """Get dependencies"""
        return ["PyMuPDF", "Pillow", "pdf2image"]
