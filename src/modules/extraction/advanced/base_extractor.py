"""
Base Extractor Interface
Ensures all extractors follow same pattern and maintain system cohesion
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class BaseExtractor(ABC):
    """
    Base class for all extractors
    Ensures consistent interface and integration points
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.validate_config()
        
    @abstractmethod
    def validate_config(self):
        """Validate extractor configuration"""
        pass
        
    @abstractmethod
    async def extract(self, pdf_path: str, document_structure: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract specific content from PDF
        
        Args:
            pdf_path: Path to PDF file
            document_structure: Pre-analyzed document structure for optimization
            
        Returns:
            Extraction results with metadata
        """
        pass
        
    @abstractmethod
    def can_process(self, document_structure: Dict[str, Any]) -> bool:
        """
        Check if this extractor should process the document
        Enables smart processing based on document content
        """
        pass
        
    def get_dependencies(self) -> List[str]:
        """Get list of dependencies this extractor needs"""
        return []
        
    def get_extraction_metadata(self) -> Dict[str, Any]:
        """Get metadata about extraction capabilities"""
        return {
            "extractor": self.__class__.__name__,
            "version": getattr(self, "VERSION", "1.0.0"),
            "capabilities": getattr(self, "CAPABILITIES", [])
        }
