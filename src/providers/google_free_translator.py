# Sửa file src/providers/google_free_translator.py

import logging
from typing import List
from googletrans import Translator
from src.providers.base_translator import BaseTranslator

logger = logging.getLogger(__name__)

class GoogleFreeTranslator(BaseTranslator):
    """Google Translate Free API implementation với Unicode fix"""
    
    def __init__(self):
        self.translator = Translator()
        self.name = "GoogleFreeTranslator"
        logger.info("Google Free Translator initialized")
    
    def _normalize_language_code(self, lang_code: str) -> str:
        """Normalize language codes to Google Translate format"""
        # Mapping common language codes
        lang_mapping = {
            'en': 'en',
            'english': 'en',
            'vi': 'vi', 
            'vietnamese': 'vi',
            'zh': 'zh',
            'chinese': 'zh',
            'ja': 'ja',
            'japanese': 'ja',
            'ko': 'ko',
            'korean': 'ko',
            'fr': 'fr',
            'french': 'fr',
            'de': 'de',
            'german': 'de',
            'es': 'es',
            'spanish': 'es',
            'auto': 'auto',
            # QUAN TRỌNG: Fix lỗi file type được gửi làm language
            'pdf': 'auto',     # ← Fix: auto-detect thay vì lỗi
            'docx': 'auto',    # ← Fix: auto-detect thay vì lỗi
            'txt': 'auto',     # ← Fix: auto-detect thay vì lỗi
            'word': 'auto',    # ← Fix thêm
        }
        
        normalized = lang_mapping.get(lang_code.lower(), lang_code)
        logger.info(f"Normalized language code: {lang_code} → {normalized}")
        return normalized
    
    async def translate(self, text: str, target_language: str, source_language: str = 'auto') -> str:
        """Translate text using Google Translate Free API"""
        try:
            # Normalize language codes
            target_lang = self._normalize_language_code(target_language)
            source_lang = self._normalize_language_code(source_language)
            
            logger.info(f"Translating: '{source_lang}' → '{target_lang}' | Text preview: {text[:50]}...")
            
            # Skip translation if target and source are the same
            if target_lang == source_lang and target_lang != 'auto':
                logger.info("Source and target languages are the same, returning original text")
                return text
            
            # Perform translation
            result = self.translator.translate(
                text, 
                src=source_lang, 
                dest=target_lang
            )
            
            translated_text = result.text
            logger.info(f"Translation result preview: {translated_text[:50]}...")
            
            return translated_text
            
        except Exception as e:
            logger.error(f"Google Free translation error: {source_language} → {target_language}: {str(e)}")
            # Return original text as fallback
            return f"[Translation failed: {str(e)}] {text}"
    
    async def translate_batch(self, texts: List[str], target_language: str, 
                            source_language: str = 'auto') -> List[str]:
        """Translate multiple texts"""
        try:
            # Normalize language codes
            target_lang = self._normalize_language_code(target_language)
            source_lang = self._normalize_language_code(source_language)
            
            logger.info(f"Batch translating {len(texts)} texts: '{source_lang}' → '{target_lang}'")
            
            results = []
            for i, text in enumerate(texts):
                try:
                    result = self.translator.translate(
                        text, 
                        src=source_lang, 
                        dest=target_lang
                    )
                    results.append(result.text)
                    logger.info(f"Batch item {i+1}/{len(texts)} completed")
                    
                except Exception as e:
                    logger.error(f"Batch translation failed for item {i+1}: {e}")
                    results.append(f"[Translation failed] {text}")
            
            return results
            
        except Exception as e:
            logger.error(f"Google Free batch translation error: {str(e)}")
            # Return original texts as fallback
            return [f"[Batch translation failed: {str(e)}] {text}" for text in texts]