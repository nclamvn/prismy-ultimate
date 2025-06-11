"""
Advanced PDF Processor Core - Updated with Text Extraction
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
    Advanced PDF processing with full document intelligence
    Now includes text extraction with layout preservation
    """
    
    VERSION = "1.1.0"
    CAPABILITIES = [
        "table_extraction",
        "image_processing",
        "text_extraction", 
        "layout_preservation",
        "ocr_processing"
    ]
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize with configuration"""
        self.config = config or {}
        self.validate_config()
        
        # Initialize document analyzer
        self._initialize_analyzer()
        
        # Initialize extractors based on config
        self._initialize_extractors()
        
        logger.info(f"AdvancedPDFProcessor initialized: v{self.VERSION}")
        
    def validate_config(self):
        """Validate configuration parameters"""
        defaults = {
            "enable_ocr": True,
            "preserve_layout": True,
            "extract_tables": True,
            "extract_images": True,
            "extract_text": True,
            "table_extraction_method": "pdfplumber",
            "compress_images": True,
            "image_format": "PNG",
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
        """Initialize extractors based on configuration"""
        from .extractors import TableExtractor, ImageExtractor, TextExtractor
        
        # Initialize text extractor
        if self.config.get("extract_text", True):
            self.text_extractor = TextExtractor({
                "preserve_layout": self.config.get("preserve_layout", True),
                "detect_paragraphs": True
            })
            logger.info("TextExtractor initialized")
        
        # Initialize table extractor
        if self.config.get("extract_tables", True):
            self.table_extractor = TableExtractor({
                "method": self.config.get("table_extraction_method", "pdfplumber")
            })
            logger.info("TableExtractor initialized")
            
        # Initialize image extractor
        if self.config.get("extract_images", True):
            self.image_extractor = ImageExtractor({
                "compress": self.config.get("compress_images", True),
                "image_format": self.config.get("image_format", "PNG")
            })
            logger.info("ImageExtractor initialized")
            
    async def process(self, data: Any) -> Any:
        """Process PDF with advanced extraction"""
        if isinstance(data, str):
            pdf_path = data
        else:
            pdf_path = data.get("path")
            
        if not pdf_path or not Path(pdf_path).exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")
            
        logger.info(f"Processing PDF: {pdf_path}")
        
        # Step 1: Analyze document structure
        document_structure = await self.structure_analyzer.analyze(pdf_path)
        logger.info(f"Document structure: {document_structure.get('page_count', 0)} pages")
        
        result = {
            "structure": document_structure,
            "text": "",
            "tables": [],
            "images": [],
            "metadata": {
                "processor_version": self.VERSION,
                "capabilities_used": []
            }
        }
        
        # Step 2: Extract text with layout
        if hasattr(self, 'text_extractor'):
            try:
                text_result = await self.text_extractor.extract(pdf_path, document_structure)
                result["text"] = text_result.get("text", "")
                result["text_layout"] = text_result.get("layout", [])
                result["metadata"]["capabilities_used"].append("text_extraction")
                logger.info(f"Text extracted: {len(result['text'])} characters")
            except Exception as e:
                logger.error(f"Text extraction failed: {e}")
        
        # Step 3: Extract tables
        if hasattr(self, 'table_extractor'):
            try:
                table_result = await self.table_extractor.extract(pdf_path, document_structure)
                result["tables"] = table_result.get("tables", [])
                result["metadata"]["capabilities_used"].append("table_extraction")
            except Exception as e:
                logger.error(f"Table extraction failed: {e}")
                
        # Step 4: Extract images
        if hasattr(self, 'image_extractor'):
            try:
                image_result = await self.image_extractor.extract(pdf_path, document_structure)
                result["images"] = image_result.get("images", [])
                result["metadata"]["capabilities_used"].append("image_extraction")
            except Exception as e:
                logger.error(f"Image extraction failed: {e}")
                
        return result
        
    def get_info(self) -> Dict[str, Any]:
        """Get module information"""
        info = {
            "name": self.__class__.__name__,
            "version": self.VERSION,
            "capabilities": self.CAPABILITIES,
            "config": self.config,
            "extractors": []
        }
        
        # List initialized extractors
        if hasattr(self, 'text_extractor'):
            info["extractors"].append("TextExtractor")
            
        if hasattr(self, 'table_extractor'):
            info["extractors"].append("TableExtractor")
            
        if hasattr(self, 'image_extractor'):
            info["extractors"].append("ImageExtractor")
            
        return info
