"""
Enhanced Translation Service with Smart Chunking
"""
import logging
from typing import Dict, Any, List, Optional
from enum import Enum
import os
from dotenv import load_dotenv

from ..modules.chunking.smart_chunker import SmartChunker, ChunkProcessor

load_dotenv()

logger = logging.getLogger(__name__)

class TranslationTier(Enum):
    BASIC = "basic"
    STANDARD = "standard" 
    PREMIUM = "premium"

class ChunkedTranslationService:
    """Translation service with smart chunking for long documents"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_client = None
        
        # Initialize chunking
        self.chunker = SmartChunker(
            chunk_size=3000,  # Optimal for GPT models
            overlap_size=200,  # Maintain context
            language="vi"      # Default to Vietnamese
        )
        self.chunk_processor = ChunkProcessor(self.chunker)
        
        if self.openai_api_key and self.openai_api_key.startswith("sk-"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ OpenAI client initialized with chunking support")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
    
    async def translate_long_document(
        self,
        text: str,
        source_lang: str = "vi",
        target_lang: str = "en",
        tier: TranslationTier = TranslationTier.STANDARD
    ) -> Dict[str, Any]:
        """
        Translate long documents using smart chunking
        """
        # Check if chunking is needed
        if len(text) < 2000:  # Small text, no chunking needed
            return await self._translate_single(text, source_lang, target_lang, tier)
            
        logger.info(f"📄 Long document detected: {len(text)} chars. Using smart chunking...")
        
        # Prepare chunks
        chunks = self.chunk_processor.prepare_for_translation(text, source_lang, target_lang)
        logger.info(f"📊 Created {len(chunks)} chunks")
        
        # Translate each chunk
        translated_chunks = []
        total_cost = 0
        total_tokens = 0
        
        for i, chunk in enumerate(chunks):
            logger.info(f"🔄 Translating chunk {i+1}/{len(chunks)}...")
            
            # Include context in translation
            chunk_text = chunk['text']
            if chunk.get('translation_context'):
                context_prompt = f"Context: {'; '.join(chunk['translation_context'])}\n\n"
            else:
                context_prompt = ""
                
            result = await self._translate_single(
                chunk_text,
                source_lang,
                target_lang,
                tier,
                context_prompt
            )
            
            if result['success']:
                chunk['translated_text'] = result['translated_text']
                total_cost += result.get('cost', 0)
                total_tokens += result.get('tokens', 0)
                translated_chunks.append(chunk)
            else:
                logger.error(f"❌ Failed to translate chunk {i+1}")
                return result  # Return error
                
        # Merge translated chunks
        merged_translation = self.chunk_processor.merge_translated_chunks(translated_chunks)
        
        return {
            "success": True,
            "tier": tier.value,
            "translated_text": merged_translation,
            "cost": total_cost,
            "tokens": total_tokens,
            "chunks_used": len(chunks),
            "chunking_method": "smart"
        }
    
    async def _translate_single(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        tier: TranslationTier,
        context: str = ""
    ) -> Dict[str, Any]:
        """Translate a single chunk of text"""
        if not self.openai_client:
            return {
                "success": False,
                "error": "No OpenAI client configured",
                "translated_text": text
            }
            
        try:
            lang_names = {
                "vi": "Vietnamese",
                "en": "English",
                "zh": "Chinese",
                "ja": "Japanese"
            }
            
            source_language = lang_names.get(source_lang, source_lang)
            target_language = lang_names.get(target_lang, target_lang)
            
            # Build prompt based on tier
            if tier == TranslationTier.PREMIUM:
                system_prompt = f"""You are an expert translator specializing in {source_language} to {target_language} translation.
                Maintain literary quality, cultural nuances, and natural flow.
                {context}"""
                model = "gpt-4"
            else:
                system_prompt = f"""Translate from {source_language} to {target_language} accurately.
                {context}"""
                model = "gpt-3.5-turbo"
                
            response = self.openai_client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            translated_text = response.choices[0].message.content
            tokens = response.usage.total_tokens
            cost = (tokens / 1000) * (0.03 if model == "gpt-4" else 0.002)
            
            return {
                "success": True,
                "translated_text": translated_text,
                "cost": cost,
                "tokens": tokens,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "translated_text": text
            }

# Update main translation service
chunked_translation_service = ChunkedTranslationService()
