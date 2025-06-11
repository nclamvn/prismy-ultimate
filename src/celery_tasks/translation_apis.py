import requests
import json
import time
import random
from typing import Dict

def google_translate_free(text: str, target: str, source: str = 'auto') -> str:
    """Use Google Translate free API"""
    try:
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': source,
            'tl': target,
            'dt': 't',
            'q': text
        }
        
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            result = json.loads(response.text)
            translated = ''
            for item in result[0]:
                if item[0]:
                    translated += item[0]
            return translated
        else:
            return f"[Error {response.status_code}] {text}"
    except Exception as e:
        print(f"Translation error: {e}")
        return f"[Error] {text}"

def translate_with_tier(text: str, source_lang: str, target_lang: str, tier: str) -> str:
    """Translate based on tier using real Google Translate"""
    
    if not text.strip():
        return text
    
    # Language code mapping
    lang_map = {
        'auto': 'auto',
        'en': 'en',
        'vi': 'vi',
        'es': 'es',
        'fr': 'fr',
        'de': 'de',
        'ja': 'ja',
        'ko': 'ko',
        'zh': 'zh-CN',
        'th': 'th',
        'id': 'id'
    }
    
    src = lang_map.get(source_lang, source_lang)
    tgt = lang_map.get(target_lang, target_lang)
    
    if tier == 'basic':
        # Quick translation, no retry
        return google_translate_free(text, tgt, src)
    
    elif tier == 'standard':
        # With retry logic
        for attempt in range(3):
            result = google_translate_free(text, tgt, src)
            if not result.startswith('[Error'):
                return result
            time.sleep(1)  # Rate limiting
        return result
    
    elif tier == 'premium':
        # Split long text into chunks for better quality
        if len(text) > 1000:
            # Split by paragraphs
            paragraphs = text.split('\n\n')
            translated_paragraphs = []
            
            for para in paragraphs:
                if para.strip():
                    # Further split if still too long
                    if len(para) > 1000:
                        sentences = para.split('. ')
                        trans_sentences = []
                        for sent in sentences:
                            if sent.strip():
                                trans = google_translate_free(sent, tgt, src)
                                trans_sentences.append(trans)
                                time.sleep(0.2)  # Rate limit
                        translated_paragraphs.append('. '.join(trans_sentences))
                    else:
                        trans = google_translate_free(para, tgt, src)
                        translated_paragraphs.append(trans)
                        time.sleep(0.2)
                else:
                    translated_paragraphs.append(para)
            
            return '\n\n'.join(translated_paragraphs)
        else:
            # Short text, translate directly
            return google_translate_free(text, tgt, src)
    
    return text
