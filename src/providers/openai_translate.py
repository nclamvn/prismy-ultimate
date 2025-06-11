# src/providers/openai_translate.py
import os
import logging
import openai
from typing import List, Optional
import asyncio

logger = logging.getLogger(__name__)

class OpenAITranslateProvider:
    """OpenAI GPT Translation provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        openai.api_key = self.api_key
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o-mini')
        
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Translate text using OpenAI"""
        try:
            system_prompt = f"""You are a professional translator. Translate the following text to {target_language}.
Maintain the original formatting, tone, and technical accuracy.
{f'Additional context: {context}' if context else ''}"""
            
            response = await asyncio.to_thread(
                openai.ChatCompletion.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=len(text) * 2  # Rough estimate
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"OpenAI translation error: {e}")
            raise
    
    async def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[str]:
        """Translate multiple texts concurrently"""
        tasks = [
            self.translate_text(text, target_language, source_language)
            for text in texts
        ]
        
        return await asyncio.gather(*tasks)
