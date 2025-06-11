"""
Advanced PDF Processor with OCR and Formula Support
"""
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class BaseModule:
    """Base class for all modules"""
    def validate_config(self):
        pass
    
    async def process(self, data: Any) -> Any:
        pass
    
    def get_info(self) -> Dict[str, Any]:
        pass

class AdvancedPDFProcessor(BaseModule):
    """
    Advanced PDF processing with OCR and Formula extraction
    """
    
    VERSION = "1.2.0"
    CAPABILITIES = [
        "table_extraction",
        "image_processing",
        "text_extraction", 
        "layout_preservation",
        "ocr_processing",
        "formula_extraction"
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration"""
        self.config = config or {}
        self.validate_config()
        
        # Initialize components
        self._initialize_analyzer()
        self._initialize_extractors()
        self._initialize_processors()
        
        logger.info(f"AdvancedPDFProcessor initialized: v{self.VERSION}")
        
    def validate_config(self):
        """Validate configuration parameters"""
        defaults = {
            "enable_ocr": True,
            "ocr_languages": ["eng", "vie"],
            "extract_formulas": True,
            "preserve_layout": True,
            "extract_tables": True,
            "extract_images": True,
            "extract_text": True,
            "max_processing_time": 300
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
                
    def _initialize_analyzer(self):
        """Initialize document structure analyzer"""
        from .analyzers import DocumentStructureAnalyzer
        self.structure_analyzer = DocumentStructureAnalyzer(self.config)
        logger.info("DocumentStructureAnalyzer initialized")
                
    def _initialize_extractors(self):
        """Initialize extractors"""
        from .extractors import TableExtractor, ImageExtractor, TextExtractor
        
        if self.config.get("extract_text", True):
            self.text_extractor = TextExtractor({
                "preserve_layout": self.config.get("preserve_layout", True)
            })
            
        if self.config.get("extract_tables", True):
            self.table_extractor = TableExtractor({
                "method": self.config.get("table_extraction_method", "pdfplumber")
            })
            
        if self.config.get("extract_images", True):
            self.image_extractor = ImageExtractor({
                "compress": self.config.get("compress_images", True)
            })
            
    def _initialize_processors(self):
        """Initialize advanced processors"""
        from .processors import OCRProcessor, FormulaProcessor
        
        if self.config.get("enable_ocr", True):
            self.ocr_processor = OCRProcessor({
                "languages": self.config.get("ocr_languages", ["eng", "vie"])
            })
            logger.info("OCRProcessor initialized")
            
        if self.config.get("extract_formulas", True):
            self.formula_processor = FormulaProcessor({
                "convert_to_latex": True
            })
            logger.info("FormulaProcessor initialized")
            
    async def process(self, data: Any) -> Any:
        """Process PDF with all features"""
        if isinstance(data, str):
            pdf_path = data
        else:
            pdf_path = data.get("path")
            
        if not pdf_path or not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
        logger.info(f"Processing PDF with OCR & Formula support: {pdf_path}")
        
        # Analyze structure
        document_structure = await self.structure_analyzer.analyze(pdf_path)
        
        result = {
            "structure": document_structure,
            "text": "",
            "tables": [],
            "images": [],
            "formulas": [],
            "ocr_text": "",
            "metadata": {
                "processor_version": self.VERSION,
                "capabilities_used": []
            }
        }
        
        # Extract text
        if hasattr(self, 'text_extractor'):
            try:
                text_result = await self.text_extractor.extract(pdf_path, document_structure)
                result["text"] = text_result.get("text", "")
                result["text_layout"] = text_result.get("layout", [])
                result["metadata"]["capabilities_used"].append("text_extraction")
            except Exception as e:
                logger.error(f"Text extraction failed: {e}")
        
        # Extract tables
        if hasattr(self, 'table_extractor'):
            try:
                table_result = await self.table_extractor.extract(pdf_path, document_structure)
                result["tables"] = table_result.get("tables", [])
                result["metadata"]["capabilities_used"].append("table_extraction")
            except Exception as e:
                logger.error(f"Table extraction failed: {e}")
                
        # Extract images
        if hasattr(self, 'image_extractor'):
            try:
                image_result = await self.image_extractor.extract(pdf_path, document_structure)
                result["images"] = image_result.get("images", [])
                result["metadata"]["capabilities_used"].append("image_extraction")
            except Exception as e:
                logger.error(f"Image extraction failed: {e}")
                
        # OCR processing
        if hasattr(self, 'ocr_processor') and result["images"]:
            try:
                logger.info("Running OCR on extracted images...")
                ocr_results = []
                
                for img in result["images"]:
                    if img.get("data"):
                        import base64
                        img_bytes = base64.b64decode(img["data"])
                        ocr_result = await self.ocr_processor.extract(img_bytes)
                        
                        if ocr_result["text"]:
                            ocr_results.append({
                                "image_id": img["id"],
                                "text": ocr_result["text"],
                                "confidence": ocr_result["metadata"]["average_confidence"]
                            })
                            
                result["ocr_results"] = ocr_results
                result["metadata"]["capabilities_used"].append("ocr_processing")
            except Exception as e:
                logger.error(f"OCR processing failed: {e}")
                
        # Formula extraction
        if hasattr(self, 'formula_processor'):
            try:
                formula_result = await self.formula_processor.extract(pdf_path, document_structure)
                result["formulas"] = formula_result.get("formulas", [])
                result["metadata"]["capabilities_used"].append("formula_extraction")
            except Exception as e:
                logger.error(f"Formula extraction failed: {e}")
                
        return result
        
    def get_info(self) -> Dict[str, Any]:
        """Get module information"""
        info = {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "capabilities": self.CAPABILITIES,
            "config": self.config,
            "extractors": [],
            "processors": []
        }
        
        # List components
        if hasattr(self, 'text_extractor'):
            info["extractors"].append("TextExtractor")
        if hasattr(self, 'table_extractor'):
            info["extractors"].append("TableExtractor")
        if hasattr(self, 'image_extractor'):
            info["extractors"].append("ImageExtractor")
        if hasattr(self, 'ocr_processor'):
            info["processors"].append("OCRProcessor")
        if hasattr(self, 'formula_processor'):
            info["processors"].append("FormulaProcessor")
            
        return info
