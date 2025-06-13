import os
from openai import OpenAI
from typing import List, Dict, Optional
from .base_translator import BaseTranslator
import logging
import asyncio

logger = logging.getLogger(__name__)

class OpenAITranslator(BaseTranslator):
    """OpenAI GPT-based translation provider"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o-mini"):
        super().__init__(api_key or os.getenv('OPENAI_API_KEY'))
        self.model = model
        if self.api_key:
            try:
                self.client = OpenAI(api_key=self.api_key)
                logger.info("OpenAI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenAI client: {e}")
                self.client = None
        else:
            self.client = None
    
    async def translate(self, text: str, target_language: str, source_language: str = 'auto') -> str:
        """Translate using OpenAI GPT"""
        try:
            if not self.client:
                raise ValueError("No OpenAI client initialized")
                
            language_name = self.get_supported_languages().get(target_language, target_language)
            
            prompt = f"""Translate the following text to {language_name}.
Only provide the translation, no explanations or notes.
Maintain the original formatting and tone.

Text: {text}"""
            
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": f"You are a professional translator. Translate accurately to {language_name}."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=len(text) * 2
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI translation error: {str(e)}")
            raise
    
    async def translate_batch(self, texts: List[str], target_language: str, source_language: str = 'auto') -> List[str]:
        """Translate multiple texts concurrently"""
        tasks = [self.translate(text, target_language, source_language) for text in texts]
        return await asyncio.gather(*tasks)
    
    def get_supported_languages(self) -> Dict[str, str]:
        """OpenAI can handle many languages"""
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
            'sv': 'Swedish',
            'da': 'Danish',
            'no': 'Norwegian',
            'fi': 'Finnish',
        }
