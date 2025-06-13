from abc import ABC, abstractmethod
from typing import List, Dict, Optional

class BaseTranslator(ABC):
    """Base class for all translation providers"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    @abstractmethod
    async def translate(self, text: str, target_language: str, source_language: str = 'auto') -> str:
        """Translate single text"""
        pass
    
    @abstractmethod
    async def translate_batch(self, texts: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """Translate multiple texts"""
        pass
    
    @abstractmethod
    def get_supported_languages(self) -> Dict[str, str]:
        """Return supported language codes"""
        pass
    
    def validate_language(self, language_code: str) -> bool:
        """Check if language is supported"""
        return language_code in self.get_supported_languages()
