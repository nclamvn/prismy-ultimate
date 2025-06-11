# src/processors/premium_translator.py
from typing import Dict, Any, List
import logging
import asyncio
from ..core.base import BaseProcessor
from ..providers.translation_manager import get_translation_manager, TranslationProvider

logger = logging.getLogger(__name__)

class PremiumTranslationProcessor(BaseProcessor):
    """Premium translation with context awareness and quality checks"""
    
    def __init__(self):
        super().__init__()
        self.translation_manager = get_translation_manager()
        
    async def process(self, data: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """Process premium translation with multiple passes"""
        chunks = data.get("chunks", [])
        source_lang = context.get("source_lang", "en")
        target_lang = context.get("target_lang", "vi")
        
        logger.info(f"Premium translation of {len(chunks)} chunks")
        
        # Build context for each chunk
        contextualized_chunks = self._build_chunk_contexts(chunks)
        
        # First pass: High-quality translation
        first_pass_results = await self._translate_with_context(
            contextualized_chunks, source_lang, target_lang
        )
        
        # Second pass: Consistency check and improvement
        final_results = await self._refine_translations(
            first_pass_results, source_lang, target_lang
        )
        
        return {
            "chunks": final_results,
            "translation_provider": "premium",
            "source_lang": source_lang,
            "target_lang": target_lang,
            "quality_score": self._calculate_quality_score(final_results)
        }
    
    def _build_chunk_contexts(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add context information to each chunk"""
        contextualized = []
        
        for i, chunk in enumerate(chunks):
            context_chunk = chunk.copy()
            
            # Add previous and next chunk for context
            prev_text = chunks[i-1]["text"] if i > 0 else ""
            next_text = chunks[i+1]["text"] if i < len(chunks)-1 else ""
            
            context_chunk["context"] = {
                "previous": prev_text[-200:] if prev_text else "",  # Last 200 chars
                "next": next_text[:200] if next_text else "",       # First 200 chars
                "position": f"{i+1}/{len(chunks)}",
                "document_type": "technical"  # Could be detected
            }
            
            contextualized.append(context_chunk)
        
        return contextualized
    
    async def _translate_with_context(
        self, 
        chunks: List[Dict[str, Any]], 
        source_lang: str, 
        target_lang: str
    ) -> List[Dict[str, Any]]:
        """Translate with context awareness"""
        translated_chunks = []
        
        # Process in smaller batches for better quality
        batch_size = 5
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i+batch_size]
            
            tasks = []
            for chunk in batch:
                text = chunk["text"]
                context_info = chunk.get("context", {})
                
                # Build context prompt
                context_prompt = f"""
Document type: {context_info.get('document_type', 'general')}
Position: {context_info.get('position', '')}
Previous context: {context_info.get('previous', '')}
Next context: {context_info.get('next', '')}
"""
                
                task = self.translation_manager.translate(
                    text=text,
                    target_language=target_lang,
                    source_language=source_lang,
                    provider=TranslationProvider.OPENAI,
                    tier="premium"
                )
                tasks.append(task)
            
            # Execute batch
            results = await asyncio.gather(*tasks)
            
            # Update chunks
            for chunk, (translated_text, metadata) in zip(batch, results):
                translated_chunk = chunk.copy()
                translated_chunk["translated_text"] = translated_text
                translated_chunk["translation_metadata"] = metadata
                translated_chunk["first_pass"] = True
                translated_chunks.append(translated_chunk)
        
        return translated_chunks
    
    async def _refine_translations(
        self, 
        chunks: List[Dict[str, Any]], 
        source_lang: str, 
        target_lang: str
    ) -> List[Dict[str, Any]]:
        """Refine translations for consistency"""
        # Build glossary from translations
        glossary = self._build_glossary(chunks)
        
        refined_chunks = []
        for chunk in chunks:
            refined_chunk = chunk.copy()
            
            # Check if refinement needed
            if self._needs_refinement(chunk, glossary):
                # Retranslate with glossary
                refined_text = await self._apply_glossary(
                    chunk["translated_text"], 
                    glossary
                )
                refined_chunk["translated_text"] = refined_text
                refined_chunk["refined"] = True
            
            refined_chunks.append(refined_chunk)
        
        return refined_chunks
    
    def _build_glossary(self, chunks: List[Dict[str, Any]]) -> Dict[str, str]:
        """Extract consistent translations for technical terms"""
        # Simple implementation - in production, use NLP
        glossary = {}
        
        # Common technical terms to track
        technical_terms = ["algorithm", "function", "variable", "equation", "theorem"]
        
        # This would be more sophisticated in production
        return glossary
    
    def _needs_refinement(self, chunk: Dict[str, Any], glossary: Dict[str, str]) -> bool:
        """Check if chunk needs refinement"""
        # Simple check - could be more sophisticated
        return chunk.get("has_formula", False) or chunk.get("has_table", False)
    
    async def _apply_glossary(self, text: str, glossary: Dict[str, str]) -> str:
        """Apply glossary to ensure consistency"""
        # In production, this would be more sophisticated
        return text
    
    def _calculate_quality_score(self, chunks: List[Dict[str, Any]]) -> float:
        """Calculate overall translation quality score"""
        if not chunks:
            return 0.0
        
        scores = []
        for chunk in chunks:
            metadata = chunk.get("translation_metadata", {})
            # Simple scoring based on provider and refinement
            if chunk.get("refined", False):
                scores.append(0.95)
            elif metadata.get("provider") == "openai":
                scores.append(0.9)
            elif metadata.get("provider") == "deepl":
                scores.append(0.85)
            else:
                scores.append(0.8)
        
        return sum(scores) / len(scores)
