# src/providers/translation_manager.py
import os
import logging
from typing import Dict, List, Optional, Tuple
from enum import Enum
import asyncio
import time

from .google_translate import GoogleTranslateProvider
from .deepl_translate import DeepLTranslateProvider
from .openai_translate import OpenAITranslateProvider

logger = logging.getLogger(__name__)

class TranslationProvider(Enum):
    GOOGLE = "google"
    DEEPL = "deepl"
    OPENAI = "openai"
    MOCK = "mock"  # For testing

class TranslationManager:
    """Manages multiple translation providers with fallback"""
    
    def __init__(self):
        self.providers = {}
        self.primary_provider = None
        self.initialize_providers()
        
    def initialize_providers(self):
        """Initialize available translation providers"""
        # Google Translate
        if os.getenv('GOOGLE_APPLICATION_CREDENTIALS'):
            try:
                provider = GoogleTranslateProvider()
                provider.initialize()
                self.providers[TranslationProvider.GOOGLE] = provider
                logger.info("Google Translate provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Google Translate: {e}")
        
        # DeepL
        if os.getenv('DEEPL_API_KEY'):
            try:
                provider = DeepLTranslateProvider()
                self.providers[TranslationProvider.DEEPL] = provider
                logger.info("DeepL provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize DeepL: {e}")
        
        # OpenAI
        if os.getenv('OPENAI_API_KEY'):
            try:
                provider = OpenAITranslateProvider()
                self.providers[TranslationProvider.OPENAI] = provider
                logger.info("OpenAI provider initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI: {e}")
        
        # Set primary provider
        if TranslationProvider.DEEPL in self.providers:
            self.primary_provider = TranslationProvider.DEEPL
        elif TranslationProvider.GOOGLE in self.providers:
            self.primary_provider = TranslationProvider.GOOGLE
        elif TranslationProvider.OPENAI in self.providers:
            self.primary_provider = TranslationProvider.OPENAI
        else:
            logger.warning("No translation providers available, using mock")
            self.primary_provider = TranslationProvider.MOCK
    
    async def translate(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
        provider: Optional[TranslationProvider] = None,
        tier: str = "standard"
    ) -> Tuple[str, Dict[str, any]]:
        """
        Translate text with automatic fallback
        Returns: (translated_text, metadata)
        """
        if not text or not text.strip():
            return text, {"provider": "none", "cached": True}
        
        # Select provider based on tier
        if provider is None:
            provider = self._select_provider_for_tier(tier)
        
        # Try primary provider first
        providers_to_try = [provider] if provider else []
        
        # Add fallback providers
        for p in self.providers.keys():
            if p not in providers_to_try:
                providers_to_try.append(p)
        
        # Try each provider
        for provider_enum in providers_to_try:
            try:
                start_time = time.time()
                
                if provider_enum == TranslationProvider.MOCK:
                    # Mock translation for testing
                    translated = f"[{target_language}] {text}"
                else:
                    provider_instance = self.providers.get(provider_enum)
                    if not provider_instance:
                        continue
                    
                    translated = await provider_instance.translate_text(
                        text=text,
                        target_language=target_language,
                        source_language=source_language
                    )
                
                duration = time.time() - start_time
                
                metadata = {
                    "provider": provider_enum.value,
                    "duration": duration,
                    "char_count": len(text),
                    "source_lang": source_language,
                    "target_lang": target_language
                }
                
                logger.info(f"Translation completed using {provider_enum.value} in {duration:.2f}s")
                return translated, metadata
                
            except Exception as e:
                logger.error(f"Translation failed with {provider_enum.value}: {e}")
                continue
        
        # All providers failed
        logger.error("All translation providers failed")
        return text, {"provider": "failed", "error": "All providers failed"}
    
    async def translate_batch(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None,
        provider: Optional[TranslationProvider] = None,
        tier: str = "standard"
    ) -> List[Tuple[str, Dict[str, any]]]:
        """Translate multiple texts efficiently"""
        if not texts:
            return []
        
        # Filter empty texts
        non_empty_indices = []
        non_empty_texts = []
        for i, text in enumerate(texts):
            if text and text.strip():
                non_empty_indices.append(i)
                non_empty_texts.append(text)
        
        if not non_empty_texts:
            return [(text, {"provider": "none"}) for text in texts]
        
        # Select provider
        if provider is None:
            provider = self._select_provider_for_tier(tier)
        
        try:
            provider_instance = self.providers.get(provider)
            if provider_instance and hasattr(provider_instance, 'translate_batch'):
                # Use batch translation if available
                start_time = time.time()
                translated_texts = await provider_instance.translate_batch(
                    texts=non_empty_texts,
                    target_language=target_language,
                    source_language=source_language
                )
                duration = time.time() - start_time
                
                # Build results
                results = []
                translated_idx = 0
                for i, text in enumerate(texts):
                    if i in non_empty_indices:
                        results.append((
                            translated_texts[translated_idx],
                            {
                                "provider": provider.value,
                                "duration": duration / len(non_empty_texts),
                                "batch": True
                            }
                        ))
                        translated_idx += 1
                    else:
                        results.append((text, {"provider": "none"}))
                
                return results
            else:
                # Fallback to individual translations
                tasks = [
                    self.translate(text, target_language, source_language, provider, tier)
                    for text in texts
                ]
                return await asyncio.gather(*tasks)
                
        except Exception as e:
            logger.error(f"Batch translation failed: {e}")
            # Fallback to individual translations
            tasks = [
                self.translate(text, target_language, source_language, provider, tier)
                for text in texts
            ]
            return await asyncio.gather(*tasks)
    
    def _select_provider_for_tier(self, tier: str) -> TranslationProvider:
        """Select appropriate provider based on tier"""
        if tier == "basic":
            # Fast providers for basic tier
            if TranslationProvider.GOOGLE in self.providers:
                return TranslationProvider.GOOGLE
            elif TranslationProvider.DEEPL in self.providers:
                return TranslationProvider.DEEPL
        elif tier == "premium":
            # High quality for premium
            if TranslationProvider.OPENAI in self.providers:
                return TranslationProvider.OPENAI
            elif TranslationProvider.DEEPL in self.providers:
                return TranslationProvider.DEEPL
        
        # Default to primary provider
        return self.primary_provider
    
    async def close(self):
        """Clean up provider resources"""
        for provider in self.providers.values():
            if hasattr(provider, 'close'):
                await provider.close()

# Global instance
_translation_manager = None

def get_translation_manager() -> TranslationManager:
    """Get or create translation manager instance"""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager
