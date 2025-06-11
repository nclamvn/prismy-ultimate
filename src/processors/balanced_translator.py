# src/processors/balanced_translator.py
from typing import Dict, Any, List
import logging
from ..core.base import BaseProcessor
from ..providers.translation_manager import get_translation_manager, TranslationProvider

logger = logging.getLogger(__name__)

class BalancedTranslationProcessor(BaseProcessor):
    """Balanced translation with quality and speed optimization"""
    
    def __init__(self):
        super().__init__()
        self.translation_manager = get_translation_manager()
        
    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process translation with balanced approach"""
        chunks = data.get("chunks", [])
        source_lang = context.get("source_lang", "en")
        target_lang = context.get("target_lang", "vi")
        
        logger.info(f"Balanced translation of {len(chunks)} chunks")
        # Handle table chunks specially
        for i, chunk in enumerate(chunks):
            if chunk.get('is_table_chunk') and chunk.get('tables'):
                # Translate table
                table = chunk['tables'][0]
                translated_table = await self._translate_table(
                    table, target_lang, source_lang
                )
                
                translated_chunks.append({
                    **chunk,
                    'tables': [translated_table],
                    'translated_text': f"[Translated table: {translated_table.get('table_id')}]",
                    'translation_metadata': {'provider': 'table_translator'}
                })
                continue


        
        # Separate chunks by type
        simple_chunks = []
        complex_chunks = []
        
        for i, chunk in enumerate(chunks):
            text = chunk.get("text", "")
            # Determine complexity
            if self._is_complex_chunk(chunk):
                complex_chunks.append((i, chunk))
            else:
                simple_chunks.append((i, chunk))
        
        # Translate simple chunks with fast provider
        simple_results = {}
        if simple_chunks:
            simple_texts = [chunk[1]["text"] for chunk in simple_chunks]
            simple_translations = await self.translation_manager.translate_batch(
                texts=simple_texts,
                target_language=target_lang,
                source_language=source_lang,
                provider=TranslationProvider.GOOGLE,
                tier="standard"
            )
            
            for (idx, _), (text, metadata) in zip(simple_chunks, simple_translations):
                simple_results[idx] = (text, metadata)
        
        # Translate complex chunks with better provider
        complex_results = {}
        if complex_chunks:
            complex_texts = [chunk[1]["text"] for chunk in complex_chunks]
            complex_translations = await self.translation_manager.translate_batch(
                texts=complex_texts,
                target_language=target_lang,
                source_language=source_lang,
                provider=TranslationProvider.DEEPL,
                tier="standard"
            )
            
            for (idx, _), (text, metadata) in zip(complex_chunks, complex_translations):
                complex_results[idx] = (text, metadata)
        
        # Combine results
        translated_chunks = []
        for i, chunk in enumerate(chunks):
            translated_chunk = chunk.copy()
            if i in simple_results:
                translated_text, metadata = simple_results[i]
            else:
                translated_text, metadata = complex_results[i]
            
            translated_chunk["translated_text"] = translated_text
            translated_chunk["translation_metadata"] = metadata
            translated_chunks.append(translated_chunk)
        
        return {
            "chunks": translated_chunks,
            "translation_provider": "balanced",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "simple_chunks": len(simple_chunks),
            "complex_chunks": len(complex_chunks)
        }
    
    def _is_complex_chunk(self, chunk: Dict[str, Any]) -> bool:
        """Determine if chunk needs premium translation"""
        text = chunk.get("text", "")
        
        # Complex if: technical content, formulas, tables, long paragraphs
        if chunk.get("has_formula", False) or chunk.get("has_table", False):
            return True
        
        if len(text) > 500:
            return True
        
        # Check for technical indicators
        technical_indicators = ["equation", "formula", "theorem", "algorithm", "$", "\\"]
        return any(indicator in text.lower() for indicator in technical_indicators)
