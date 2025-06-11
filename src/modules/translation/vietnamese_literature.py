"""
Special handler for Vietnamese literature translation
Preserves cultural context and literary style
"""

class VietnameseLiteratureTranslator:
    """Specialized translator for Vietnamese literary works"""
    
    def __init__(self):
        self.known_works = {
            "chí phèo": {
                "author": "Nam Cao",
                "era": "1941",
                "style": "realist",
                "context": "Vietnamese village life, social criticism"
            }
        }
    
    def get_context_prompt(self, text: str, target_lang: str) -> str:
        """Generate context-aware prompt for literary translation"""
        
        # Detect if this is Chí Phèo
        if "chí phèo" in text.lower() or "nam cao" in text.lower():
            return f"""You are translating a classic Vietnamese literary work "Chí Phèo" by Nam Cao.
This is a realist story about rural Vietnamese society in the 1940s.

Guidelines:
- Preserve the literary style and tone
- Keep cultural references with explanations
- Maintain the social criticism elements
- Character names like "Chí Phèo" should be kept with explanation
- Village terminology should be translated with cultural context

Translate to {target_lang} while preserving the literary merit:"""
        
        return f"Translate this Vietnamese literary text to {target_lang}, preserving style and cultural context:"
