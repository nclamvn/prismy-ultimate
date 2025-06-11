# src/providers/deepl_translate.py
import os
import logging
import aiohttp
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class DeepLTranslateProvider:
    """DeepL Translation API provider"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('DEEPL_API_KEY')
        self.base_url = "https://api-free.deepl.com/v2"  # Use paid endpoint for production
        self.session = None
        
    async def initialize(self):
        """Initialize aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                headers={"Authorization": f"DeepL-Auth-Key {self.api_key}"}
            )
    
    async def close(self):
        """Close aiohttp session"""
        if self.session:
            await self.session.close()
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """Translate text using DeepL"""
        await self.initialize()
        
        try:
            params = {
                "text": text,
                "target_lang": target_language.upper()
            }
            
            if source_language:
                params["source_lang"] = source_language.upper()
            
            async with self.session.post(
                f"{self.base_url}/translate",
                data=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"DeepL API error: {error_text}")
                
                data = await response.json()
                return data["translations"][0]["text"]
                
        except Exception as e:
            logger.error(f"DeepL translation error: {e}")
            raise
    
    async def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[str]:
        """Translate multiple texts in batch"""
        await self.initialize()
        
        try:
            params = {
                "text": texts,  # DeepL accepts array
                "target_lang": target_language.upper()
            }
            
            if source_language:
                params["source_lang"] = source_language.upper()
            
            async with self.session.post(
                f"{self.base_url}/translate",
                json=params
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise Exception(f"DeepL API error: {error_text}")
                
                data = await response.json()
                return [t["text"] for t in data["translations"]]
                
        except Exception as e:
            logger.error(f"DeepL batch translation error: {e}")
            raise
    
    async def get_usage(self) -> Dict[str, int]:
        """Get API usage statistics"""
        await self.initialize()
        
        try:
            async with self.session.get(f"{self.base_url}/usage") as response:
                if response.status != 200:
                    return {}
                
                data = await response.json()
                return {
                    "character_count": data.get("character_count", 0),
                    "character_limit": data.get("character_limit", 0)
                }
        except Exception as e:
            logger.error(f"Error getting usage: {e}")
            return {}
