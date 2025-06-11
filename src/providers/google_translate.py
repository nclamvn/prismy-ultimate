# src/providers/google_translate.py
import os
import logging
from typing import Dict, List, Optional
from google.cloud import translate_v3 as translate
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

class GoogleTranslateProvider:
    """Google Cloud Translation API provider"""
    
    def __init__(self, credentials_path: Optional[str] = None):
        self.credentials_path = credentials_path or os.getenv('GOOGLE_APPLICATION_CREDENTIALS')
        self.client = None
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT', 'prismy-translation')
        
    def initialize(self):
        """Initialize Google Translate client"""
        try:
            if self.credentials_path:
                credentials = service_account.Credentials.from_service_account_file(
                    self.credentials_path
                )
                self.client = translate.TranslationServiceClient(credentials=credentials)
            else:
                # Use default credentials
                self.client = translate.TranslationServiceClient()
            
            logger.info("Google Translate client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Translate: {e}")
            raise
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """Translate text using Google Translate"""
        if not self.client:
            self.initialize()
        
        try:
            parent = f"projects/{self.project_id}/locations/global"
            
            response = self.client.translate_text(
                parent=parent,
                contents=[text],
                target_language_code=target_language,
                source_language_code=source_language,
                mime_type="text/plain"
            )
            
            return response.translations[0].translated_text
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            raise
    
    async def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[str]:
        """Translate multiple texts in batch"""
        if not self.client:
            self.initialize()
        
        try:
            parent = f"projects/{self.project_id}/locations/global"
            
            response = self.client.translate_text(
                parent=parent,
                contents=texts,
                target_language_code=target_language,
                source_language_code=source_language,
                mime_type="text/plain"
            )
            
            return [t.translated_text for t in response.translations]
            
        except Exception as e:
            logger.error(f"Batch translation error: {e}")
            raise
    
    def get_supported_languages(self) -> List[Dict[str, str]]:
        """Get list of supported languages"""
        if not self.client:
            self.initialize()
        
        try:
            parent = f"projects/{self.project_id}/locations/global"
            response = self.client.get_supported_languages(parent=parent)
            
            return [
                {
                    "code": lang.language_code,
                    "name": lang.display_name
                }
                for lang in response.languages
            ]
        except Exception as e:
            logger.error(f"Error getting languages: {e}")
            return []
