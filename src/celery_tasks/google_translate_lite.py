import requests
import json
import time

def google_translate_free(text: str, target: str, source: str = 'auto') -> str:
    """Use Google Translate free API (limited)"""
    try:
        # Google Translate free endpoint
        url = "https://translate.googleapis.com/translate_a/single"
        params = {
            'client': 'gtx',
            'sl': source,
            'tl': target,
            'dt': 't',
            'q': text
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            result = json.loads(response.text)
            # Extract translated text
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

# Test it
if __name__ == "__main__":
    test = google_translate_free("Hello world", "vi", "en")
    print(f"Test: {test}")
