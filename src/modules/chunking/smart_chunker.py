"""
Smart Chunking System - PRISMY Core Feature
Intelligent text splitting that preserves context and meaning
"""
import re
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class SmartChunker:
    """
    Advanced text chunking with context preservation
    Key features:
    - Semantic boundary detection
    - Context overlap
    - Metadata preservation
    - Multi-language support
    """
    
    def __init__(
        self, 
        chunk_size: int = 3000,
        overlap_size: int = 200,
        language: str = "vi"
    ):
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.language = language
        
        # Sentence endings for different languages
        self.sentence_endings = {
            "vi": [".", "!", "?", "。", "！", "？"],  # Vietnamese + Chinese punctuation
            "en": [".", "!", "?"],
            "default": [".", "!", "?", "。", "！", "？", "।", "।"]
        }
        
    def chunk_text(self, text: str, preserve_paragraphs: bool = True) -> List[Dict[str, Any]]:
        """
        Smart chunk text while preserving meaning
        
        Args:
            text: Input text to chunk
            preserve_paragraphs: Try to keep paragraphs together
            
        Returns:
            List of chunks with metadata
        """
        if not text or len(text) <= self.chunk_size:
            return [{
                "text": text,
                "index": 0,
                "start_char": 0,
                "end_char": len(text),
                "has_continuation": False
            }]
        
        # Preprocess text
        text = self._normalize_whitespace(text)
        
        if preserve_paragraphs:
            chunks = self._chunk_by_paragraphs(text)
        else:
            chunks = self._chunk_by_sentences(text)
            
        # Add overlap between chunks
        chunks = self._add_overlap(chunks, text)
        
        # Add metadata
        chunks = self._add_metadata(chunks)
        
        logger.info(f"Created {len(chunks)} chunks from {len(text)} characters")
        return chunks
    
    def _normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace while preserving paragraph breaks"""
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        # Preserve paragraph breaks (multiple newlines)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        # Remove trailing whitespace
        text = '\n'.join(line.rstrip() for line in text.split('\n'))
        return text.strip()
    
    def _chunk_by_paragraphs(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text trying to preserve paragraph boundaries"""
        chunks = []
        paragraphs = text.split('\n\n')
        
        current_chunk = ""
        start_char = 0
        
        for i, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
                
            # Check if adding this paragraph exceeds chunk size
            if current_chunk and len(current_chunk) + len(para) + 2 > self.chunk_size:
                # Save current chunk
                chunks.append({
                    "text": current_chunk.strip(),
                    "start_char": start_char,
                    "end_char": start_char + len(current_chunk)
                })
                
                # Start new chunk
                current_chunk = para
                start_char = start_char + len(current_chunk) + 2
            else:
                # Add to current chunk
                if current_chunk:
                    current_chunk += "\n\n" + para
                else:
                    current_chunk = para
        
        # Add last chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "start_char": start_char,
                "end_char": start_char + len(current_chunk)
            })
            
        # If paragraphs are too long, further split by sentences
        final_chunks = []
        for chunk in chunks:
            if len(chunk["text"]) > self.chunk_size * 1.5:
                sub_chunks = self._chunk_by_sentences(chunk["text"])
                final_chunks.extend(sub_chunks)
            else:
                final_chunks.append(chunk)
                
        return final_chunks
    
    def _chunk_by_sentences(self, text: str) -> List[Dict[str, Any]]:
        """Chunk text by sentence boundaries"""
        endings = self.sentence_endings.get(self.language, self.sentence_endings["default"])
        
        # Create regex pattern for sentence endings
        pattern = f"[{''.join(re.escape(e) for e in endings)}]"
        sentences = re.split(f"({pattern})", text)
        
        # Reconstruct sentences (join text with its ending punctuation)
        full_sentences = []
        for i in range(0, len(sentences)-1, 2):
            if i+1 < len(sentences):
                full_sentences.append(sentences[i] + sentences[i+1])
            else:
                full_sentences.append(sentences[i])
                
        chunks = []
        current_chunk = ""
        start_char = 0
        
        for sentence in full_sentences:
            sentence = sentence.strip()
            if not sentence:
                continue
                
            if current_chunk and len(current_chunk) + len(sentence) + 1 > self.chunk_size:
                chunks.append({
                    "text": current_chunk.strip(),
                    "start_char": start_char,
                    "end_char": start_char + len(current_chunk)
                })
                
                current_chunk = sentence
                start_char = start_char + len(current_chunk) + 1
            else:
                if current_chunk:
                    current_chunk += " " + sentence
                else:
                    current_chunk = sentence
                    
        # Add last chunk
        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "start_char": start_char,
                "end_char": start_char + len(current_chunk)
            })
            
        return chunks
    
    def _add_overlap(self, chunks: List[Dict[str, Any]], original_text: str) -> List[Dict[str, Any]]:
        """Add overlap between chunks for context preservation"""
        if len(chunks) <= 1:
            return chunks
            
        overlapped_chunks = []
        
        for i, chunk in enumerate(chunks):
            new_chunk = chunk.copy()
            
            # Add overlap from previous chunk
            if i > 0 and self.overlap_size > 0:
                prev_text = chunks[i-1]["text"]
                overlap_text = prev_text[-self.overlap_size:]
                
                # Find word boundary for clean overlap
                space_pos = overlap_text.find(' ')
                if space_pos > 0:
                    overlap_text = overlap_text[space_pos+1:]
                    
                new_chunk["text"] = overlap_text + " " + new_chunk["text"]
                new_chunk["overlap_start"] = len(overlap_text)
            else:
                new_chunk["overlap_start"] = 0
                
            overlapped_chunks.append(new_chunk)
            
        return overlapped_chunks
    
    def _add_metadata(self, chunks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add metadata to chunks"""
        total_chunks = len(chunks)
        
        for i, chunk in enumerate(chunks):
            chunk["index"] = i
            chunk["total_chunks"] = total_chunks
            chunk["has_continuation"] = i < total_chunks - 1
            chunk["chunk_size"] = len(chunk["text"])
            
            # Add context hints
            if i == 0:
                chunk["position"] = "start"
            elif i == total_chunks - 1:
                chunk["position"] = "end"
            else:
                chunk["position"] = "middle"
                
        return chunks
    
    def merge_chunks(self, chunks: List[str], remove_overlap: bool = True) -> str:
        """Merge chunks back into original text"""
        if not chunks:
            return ""
            
        if not remove_overlap:
            return " ".join(chunks)
            
        # Smart merge removing overlaps
        merged = chunks[0]
        
        for i in range(1, len(chunks)):
            current = chunks[i]
            
            # Find overlap between end of merged and start of current
            overlap_found = False
            for overlap_size in range(min(self.overlap_size * 2, len(merged), len(current)), 0, -1):
                if merged.endswith(current[:overlap_size]):
                    merged += current[overlap_size:]
                    overlap_found = True
                    break
                    
            if not overlap_found:
                merged += " " + current
                
        return merged

class ChunkProcessor:
    """Process chunks for translation while maintaining context"""
    
    def __init__(self, chunker: Optional[SmartChunker] = None):
        self.chunker = chunker or SmartChunker()
        
    def prepare_for_translation(
        self, 
        text: str,
        source_lang: str = "vi",
        target_lang: str = "en"
    ) -> List[Dict[str, Any]]:
        """
        Prepare text chunks for translation with context
        """
        # Chunk the text
        chunks = self.chunker.chunk_text(text)
        
        # Add translation context to each chunk
        for i, chunk in enumerate(chunks):
            context = []
            
            # Add previous chunk summary for context
            if i > 0:
                context.append(f"Previous context: {chunks[i-1]['text'][-100:]}")
                
            # Add next chunk preview for context
            if i < len(chunks) - 1:
                context.append(f"Continues with: {chunks[i+1]['text'][:100]}")
                
            chunk["translation_context"] = context
            chunk["source_lang"] = source_lang
            chunk["target_lang"] = target_lang
            
        return chunks
    
    def merge_translated_chunks(
        self,
        translated_chunks: List[Dict[str, Any]],
        remove_overlap: bool = True
    ) -> str:
        """Merge translated chunks back together"""
        texts = [chunk.get("translated_text", chunk.get("text", "")) for chunk in translated_chunks]
        return self.chunker.merge_chunks(texts, remove_overlap)

# Convenience functions
def smart_chunk_text(
    text: str,
    chunk_size: int = 3000,
    overlap_size: int = 200,
    language: str = "vi"
) -> List[Dict[str, Any]]:
    """Convenience function for smart chunking"""
    chunker = SmartChunker(chunk_size, overlap_size, language)
    return chunker.chunk_text(text)
