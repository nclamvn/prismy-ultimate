"""
Enhanced Translation Service with Smart Chunking - Fixed
"""
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
import os
from dotenv import load_dotenv

# Import smart chunking
from ..modules.chunking.smart_chunker import SmartChunker, ChunkProcessor

load_dotenv()

logger = logging.getLogger(__name__)

class TranslationTier(Enum):
    BASIC = "basic"
    STANDARD = "standard" 
    PREMIUM = "premium"

class TranslationService:
    """AI-powered translation service with smart chunking"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "").strip()
        self.openai_client = None
        
        # Initialize chunking system
        self.chunker = SmartChunker(
            chunk_size=3000,     # Optimal for GPT
            overlap_size=200,    # Good context preservation
            language="vi"        # Default Vietnamese
        )
        self.chunk_processor = ChunkProcessor(self.chunker)
        
        if self.openai_api_key and self.openai_api_key.startswith("sk-"):
            try:
                from openai import OpenAI
                self.openai_client = OpenAI(api_key=self.openai_api_key)
                logger.info("✅ OpenAI client initialized with smart chunking")
            except Exception as e:
                logger.error(f"❌ Failed to initialize OpenAI: {e}")
        else:
            logger.warning("⚠️ No valid OpenAI API key found")
            
    async def translate(
        self,
        text: str,
        source_lang: str = "auto",
        target_lang: str = "vi",
        tier: TranslationTier = TranslationTier.BASIC,
        use_chunking: bool = True
    ) -> Dict[str, Any]:
        """
        Translate text with automatic chunking for long documents
        """
        # Language mapping
        lang_names = {
            "vi": "Vietnamese",
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "fr": "French",
            "es": "Spanish",
            "de": "German"
        }
        
        target_language = lang_names.get(target_lang, target_lang)
        
        # Check if we need chunking
        if use_chunking and len(text) > 2000:
            logger.info(f"📄 Long document ({len(text)} chars), using smart chunking...")
            return await self._translate_chunked(text, source_lang, target_lang, tier)
        else:
            # Single chunk translation
            return await self._translate_single(text, target_language, tier)
    
    async def _translate_chunked(
        self,
        text: str,
        source_lang: str,
        target_lang: str,
        tier: TranslationTier
    ) -> Dict[str, Any]:
        """Handle translation of long documents with chunking"""
        
        # Language names for prompts
        lang_names = {
            "vi": "Vietnamese",
            "en": "English",
            "zh": "Chinese",
            "ja": "Japanese",
            "ko": "Korean",
            "fr": "French",
            "es": "Spanish",
            "de": "German"
        }
        
        # Prepare chunks with context
        chunks = self.chunk_processor.prepare_for_translation(text, source_lang, target_lang)
        logger.info(f"📊 Created {len(chunks)} chunks for translation")
        
        translated_chunks = []
        total_cost = 0
        total_tokens = 0
        errors = []
        
        for i, chunk in enumerate(chunks):
            # Get chunk size safely
            chunk_size = len(chunk.get('text', ''))
            logger.info(f"🔄 Translating chunk {i+1}/{len(chunks)} ({chunk_size} chars)...")
            
            # Build context-aware prompt
            context = ""
            if chunk.get('translation_context'):
                context = f"Context: {'; '.join(chunk['translation_context'])}\n\n"
            
            # Translate chunk
            result = await self._translate_single(
                chunk['text'],
                lang_names.get(target_lang, target_lang),
                tier,
                context
            )
            
            if result['success']:
                chunk['translated_text'] = result['translated_text']
                translated_chunks.append(chunk)
                total_cost += result.get('cost', 0)
                total_tokens += result.get('tokens', 0)
            else:
                errors.append(f"Chunk {i+1}: {result.get('error', 'Unknown error')}")
                # Use original text as fallback
                chunk['translated_text'] = chunk['text']
                translated_chunks.append(chunk)
        
        # Merge translated chunks
        if translated_chunks:
            merged_text = self.chunk_processor.merge_translated_chunks(translated_chunks)
            
            return {
                "success": len(errors) == 0,
                "tier": tier.value,
                "translated_text": merged_text,
                "cost": total_cost,
                "tokens": total_tokens,
                "chunks_used": len(chunks),
                "errors": errors if errors else None,
                "chunking_method": "smart"
            }
        else:
            return {
                "success": False,
                "error": "No chunks could be translated",
                "translated_text": text
            }
    
    async def _translate_single(
        self,
        text: str,
        target_lang: str,
        tier: TranslationTier,
        context: str = ""
    ) -> Dict[str, Any]:
        """Translate a single piece of text"""
        
        if not self.openai_client:
            return self._mock_translation(text, target_lang, tier)
            
        try:
            # Select model and prompt based on tier
            if tier == TranslationTier.PREMIUM:
                model = "gpt-4"
                system_prompt = f"""{context}You are an expert translator specializing in literary works.
                Translate to {target_lang} while:
                - Preserving cultural nuances and literary style
                - Maintaining the author's voice and tone
                - Keeping proper names with explanations when needed
                - Ensuring the translation reads naturally in {target_lang}"""
            elif tier == TranslationTier.STANDARD:
                model = "gpt-3.5-turbo"
                system_prompt = f"""{context}You are a professional translator.
                Translate to {target_lang} accurately while maintaining readability and natural flow."""
            else:  # BASIC
                model = "gpt-3.5-turbo"
                system_prompt = f"{context}Translate the following text to {target_lang}:"
            
            # Make API call
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
            total_tokens = response.usage.total_tokens
            
            # Calculate cost
            if model == "gpt-4":
                cost_per_1k = 0.03
            else:
                cost_per_1k = 0.002
            
            cost = (total_tokens / 1000) * cost_per_1k
            
            return {
                "success": True,
                "tier": tier.value,
                "translated_text": translated_text,
                "cost": cost,
                "tokens": total_tokens,
                "model": model
            }
            
        except Exception as e:
            logger.error(f"Translation error: {e}")
            return {
                "success": False,
                "error": str(e),
                "translated_text": text[:200] + "...",
                "tier": tier.value
            }
    
    def _mock_translation(self, text: str, target_lang: str, tier: TranslationTier) -> Dict[str, Any]:
        """Mock translation for testing"""
        return {
            "success": True,
            "tier": tier.value,
            "translated_text": f"[MOCK {tier.value} to {target_lang}] {text[:200]}...",
            "cost": 0.001,
            "mock": True,
            "message": "No API key configured. Add OPENAI_API_KEY to .env file."
        }

# Singleton instance
translation_service = TranslationService()
