"""
FILE: rag/multilingual/translator.py
PURPOSE: Translate farmer questions between English and Nigerian languages

SUPPORTED LANGUAGES:
    - yo: Yoruba
    - ha: Hausa  
    - ig: Igbo
    - pcm: Nigerian Pidgin English
    - ar: Arabic
    - fr: French
    - en: English

HOW IT WORKS:
    Uses Google Translate API (more accurate for African languages)
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

# Import Google Translate
try:
    from deep_translator import GoogleTranslator
    GOOGLE_TRANSLATE_AVAILABLE = True
except ImportError:
    GOOGLE_TRANSLATE_AVAILABLE = False
    print("⚠️ Run: pip install deep-translator")

from config.loader import config
from logger.custom_logger import get_logger

logger = get_logger(__name__).logger


class LanguageTranslator:
    """Translates between English and Nigerian languages using Google Translate."""
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern - only one instance."""
        if cls._instance is None:
            logger.info('=' * 50)
            logger.info('🌍 CREATING LANGUAGE TRANSLATOR')
            logger.info('=' * 50)
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize translator with language mappings."""
        
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        logger.info('Initializing Language Translator...')
        
        # Load language configuration
        language_config = config.get('languages', {})
        self.supported_languages = language_config.get('supported', [])
        self.default_language = language_config.get('default', 'en')
        
        # Build language mapping dictionary
        self.lang_map = {}
        for lang in self.supported_languages:
            code = lang.get('code', '')
            name = lang.get('name', '')
            if code and name:
                self.lang_map[code] = name
        
        # Map for Google Translate
        self.google_map = {
            'en': 'en', 'yo': 'yo', 'ha': 'ha', 'ig': 'ig',
            'ar': 'ar', 'fr': 'fr', 'pcm': 'en'
        }
        
        self.is_ready = GOOGLE_TRANSLATE_AVAILABLE
        
        logger.info(f'  Supported languages: {list(self.lang_map.keys())}')
        logger.info(f'  Google Translate: {"✅ Available" if self.is_ready else "❌ Not installed"}')
        logger.info('=' * 50)
        logger.info('🌍 TRANSLATOR READY')
        logger.info('=' * 50)
    
    # ============================================================
    # TRANSLATE USING GOOGLE TRANSLATE
    # ============================================================
    def translate(self, text: str, source_lang: str, target_lang: str) -> str:
        """Translate text from source language to target language."""
        
        # If same language or no text, return original
        if source_lang == target_lang or not text:
            return text
        
        # If translator not ready, return original
        if not self.is_ready:
            return text
        
        # Map language codes for Google Translate
        source = self.google_map.get(source_lang, 'en')
        target = self.google_map.get(target_lang, 'en')
        
        try:
            translator = GoogleTranslator(source=source, target=target)
            translated = translator.translate(text)
            logger.debug(f'  Translated: {source_lang} → {target_lang}')
            return translated
        except Exception as e:
            logger.error(f'  Translation failed: {e}')
            return text
    
    # ============================================================
    # CONVERT FARMER QUESTION TO ENGLISH
    # ============================================================
    def to_english(self, text: str, source_lang: str = None) -> Tuple[str, str]:
        """Convert farmer's question to English for searching."""
        
        # Detect language if not provided
        if source_lang is None:
            source_lang = 'en'  # Default to English
        
        # If already English, return as-is
        if source_lang == 'en':
            return text, source_lang
        
        # Translate to English
        english_text = self.translate(text, source_lang, 'en')
        return english_text, source_lang
    
    # ============================================================
    # CONVERT ENGLISH ANSWER BACK TO FARMER'S LANGUAGE
    # ============================================================
    def from_english(self, text: str, target_lang: str) -> str:
        """Convert English answer back to farmer's language."""
        
        # If target is English, return as-is
        if target_lang == 'en' or not text:
            return text
        
        # Translate to target language
        return self.translate(text, 'en', target_lang)
    
    # ============================================================
    # GET READABLE LANGUAGE NAME
    # ============================================================
    def get_language_name(self, lang_code: str) -> str:
        """Get the readable name of a language code."""
        return self.lang_map.get(lang_code, 'English')


# ============================================================
# SINGLETON INSTANCE
# ============================================================
translator = LanguageTranslator()


# ============================================================
# TEST BLOCK WITH 3 EXAMPLES
# ============================================================
if __name__ == '__main__':
    print('\n' + '=' * 70)
    print('🌍 TESTING LANGUAGE TRANSLATOR (Google Translate)')
    print('=' * 70)
    
    trans = LanguageTranslator()
    
    if not trans.is_ready:
        print('\n⚠️ Google Translate not installed. Run: pip install deep-translator')
        exit(1)
    
    print(f'\n✅ Translator Ready')
    print(f'   Supported: {list(trans.lang_map.keys())}')
    
    # ============================================================
    # EXAMPLE 1: English to Yoruba
    # ============================================================
    print('\n' + '=' * 70)
    print('📝 EXAMPLE 1: English → Yoruba (Farmer Question)')
    print('=' * 70)
    
    english_text = "How to treat cassava mosaic disease?"
    yoruba_text = trans.translate(english_text, 'en', 'yo')
    
    print(f'\n  English: {english_text}')
    print(f'  Yoruba:  {yoruba_text}')
    
    # ============================================================
    # EXAMPLE 2: English to Hausa
    # ============================================================
    print('\n' + '=' * 70)
    print('📝 EXAMPLE 2: English → Hausa (Farmer Question)')
    print('=' * 70)
    
    english_text = "What is the best way to plant rice?"
    hausa_text = trans.translate(english_text, 'en', 'ha')
    
    print(f'\n  English: {english_text}')
    print(f'  Hausa:   {hausa_text}')
    
    # ============================================================
    # EXAMPLE 3: Full Pipeline (Question → Search → Answer → Native)
    # ============================================================
    print('\n' + '=' * 70)
    print('📝 EXAMPLE 3: Full RAG Pipeline (Yoruba Farmer)')
    print('=' * 70)
    
    # Step 1: Farmer asks in Yoruba
    yoruba_question = "Báwo ni a ṣe le tójú àrùn ẹ̀gẹ́?"
    print(f'\n  Step 1 - Farmer asks (Yoruba): {yoruba_question}')
    
    # Step 2: Translate to English for searching
    english_question, detected_lang = trans.to_english(yoruba_question, 'yo')
    print(f'  Step 2 - Translated to English: {english_question}')
    
    # Step 3: RAG system searches and gets answer (simulated)
    english_answer = "Remove infected plants immediately. Use resistant varieties like TME 419. Apply neem oil to control whiteflies."
    print(f'  Step 3 - RAG finds answer (English): {english_answer}')
    
    # Step 4: Translate answer back to Yoruba
    yoruba_answer = trans.from_english(english_answer, 'yo')
    print(f'  Step 4 - Answer in Yoruba: {yoruba_answer}')
    
    # ============================================================
    # BONUS: Test all supported languages
    # ============================================================
    print('\n' + '=' * 70)
    print('📝 BONUS: "Hello, how are you?" in all languages')
    print('=' * 70)
    
    test_phrase = "Hello, how are you?"
    languages = [
        ('yo', 'Yoruba'),
        ('ha', 'Hausa'),
        ('ig', 'Igbo'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
        ('pcm', 'Pidgin English')
    ]
    
    for code, name in languages:
        translated = trans.translate(test_phrase, 'en', code)
        print(f'  {name:12} ({code}): {translated}')
    
    # Final summary
    print('\n' + '=' * 70)
    print('✅ TRANSLATOR READY - Phase 9 Complete!')
    print('=' * 70)