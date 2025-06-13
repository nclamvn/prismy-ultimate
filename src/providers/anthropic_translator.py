import os
import anthropic
from typing import List, Dict, Optional
from .base_translator import BaseTranslator
import logging
import asyncio

logger = logging.getLogger(__name__)

class AnthropicTranslator(BaseTranslator):
    """Anthropic Claude-based translation provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-haiku-20240307"):
        super().__init__(api_key or os.getenv('ANTHROPIC_API_KEY'))
        self.model = model
        if self.api_key:
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                logger.info("Anthropic client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Anthropic client: {e}")
                self.client = None
        else:
            self.client = None
    
    async def translate(self, text: str, target_language: str, source_language: str = 'auto') -> str:
        """Translate using Claude"""
        try:
            if not self.client:
                raise ValueError("No Anthropic client initialized")
            
            language_name = self.get_supported_languages().get(target_language, target_language)
            
            prompt = f"""Translate the following text to {language_name}.
Provide only the translation without any explanations or notes.
Preserve the original formatting, tone, and style.

Text to translate: {text}"""
            
            response = await asyncio.to_thread(
                self.client.messages.create,
                model=self.model,
                max_tokens=len(text) * 3,
                temperature=0.3,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            return response.content[0].text.strip()
            
        except Exception as e:
            logger.error(f"Anthropic translation error: {str(e)}")
            raise
    
    async def translate_batch(self, texts: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """Translate multiple texts"""
        tasks = [self.translate(text, target_language, source_language) for text in texts]
        return await asyncio.gather(*tasks)
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Claude supports many languages"""
        return {
            'vi': 'Vietnamese',
            'en': 'English',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'ja': 'Japanese',
            'ko': 'Korean',
            'zh': 'Chinese',
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
            'he': 'Hebrew',
            'cs': 'Czech',
            'hu': 'Hungarian',
            'ro': 'Romanian',
        }
