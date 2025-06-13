import os
from typing import List, Dict, Optional
from google.cloud import translate_v2 as translate
from google.oauth2 import service_account
from .base_translator import BaseTranslator
import logging

logger = logging.getLogger(__name__)

class GoogleTranslator(BaseTranslator):
    """Google Cloud Translation API provider"""
    
    def __init__(self, api_key: Optional[str] = None, credentials_path: Optional[str] = None):
        super().__init__(api_key)
        
        # Try environment variables first
        if not credentials_path:
            credentials_path = os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        
        try:
            if credentials_path and os.path.exists(credentials_path):
                credentials = service_account.Credentials.from_service_account_file(credentials_path)
                self.client = translate.Client(credentials=credentials)
            else:
                # Use API key method
                self.client = translate.Client()
        except Exception as e:
            logger.warning(f"Failed to initialize Google Translate client: {e}")
            self.client = None
    
    async def translate(self, text: str, target_language: str, source_language: str = 'auto') -> str:
        """Translate single text using Google Translate"""
        try:
            if not self.client:
                raise ValueError("Google Translate client not initialized")
                
            if source_language == 'auto':
                source_language = None
            
            result = self.client.translate(
                text,
                target_language=target_language,
                source_language=source_language
            )
            
            return result['translatedText']
            
        except Exception as e:
            logger.error(f"Google Translate error: {str(e)}")
            # Fallback to mock translation
            return f"[GT-{target_language.upper()}] {text}"
    
    async def translate_batch(self, texts: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """Translate multiple texts in batch"""
        try:
            if not self.client:
                raise ValueError("Google Translate client not initialized")
                
            if source_language == 'auto':
                source_language = None
            
            results = self.client.translate(
                texts,
                target_language=target_language,
                source_language=source_language
            )
            
            return [r['translatedText'] for r in results]
            
        except Exception as e:
            logger.error(f"Google Translate batch error: {str(e)}")
            # Fallback to mock translation
            return [f"[GT-{target_language.upper()}] {text}" for text in texts]
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Return Google Translate supported languages"""
        return {
            'vi': 'Vietnamese',
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese (Simplified)',
            'zh-TW': 'Chinese (Traditional)',
            'th': 'Thai',
            'id': 'Indonesian',
            'ms': 'Malay',
            'pt': 'Portuguese',
            'ru': 'Russian',
            'ar': 'Arabic',
            'hi': 'Hindi',
            'it': 'Italian',
            'nl': 'Dutch',
            'pl': 'Polish',
            'tr': 'Turkish',
        }
