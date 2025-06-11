# src/processors/google_translator.py
from typing import Dict, Any, List
import logging
from ..core.base import BaseProcessor
from ..providers.translation_manager import get_translation_manager, TranslationProvider

logger = logging.getLogger(__name__)

class GoogleTranslationProcessor(BaseProcessor):
    """Basic translation using Google Translate API"""
    
    def __init__(self):
        super().__init__()
        self.translation_manager = get_translation_manager()
        
    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process translation using Google Translate"""
        chunks = data.get("chunks", [])
        source_lang = context.get("source_lang", "en")
        target_lang = context.get("target_lang", "vi")
        
        logger.info(f"Translating {len(chunks)} chunks from {source_lang} to {target_lang}")
        
        # Extract texts
        texts = [chunk.get("text", "") for chunk in chunks]
        
        # Batch translate
        translations = await self.translation_manager.translate_batch(
            texts=texts,
            target_language=target_lang,
            source_language=source_lang,
            tier="basic"
        )
        
        # Update chunks with translations
        translated_chunks = []
        for chunk, (translated_text, metadata) in zip(chunks, translations):
            translated_chunk = chunk.copy()
            translated_chunk["translated_text"] = translated_text
            translated_chunk["translation_metadata"] = metadata
            translated_chunks.append(translated_chunk)
        
        return {
            "chunks": translated_chunks,
            "translation_provider": "google",
            "source_lang": source_lang,
            "target_lang": target_lang
        }
