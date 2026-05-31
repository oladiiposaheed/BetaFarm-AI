'''
 Helper functions for translation caching

PURPOSE:
    Provides utility functions for:
    - Generating cache keys (unique identifiers)
    - Checking database cache
    - Saving to database cache
    - Detecting language from text

'''

import hashlib
from .models import TranslationCache

#Generate Unique Hash key for cache lookup
def get_cache_key(text, source_lang, target_lang):
    
    #Combine all three values into one string
    key_string = f'{text}_{source_lang}_{target_lang}'
    
    #Convert string to bytes
    key_bytes = key_string.encode('utf-8')
    
    #Create MD5 hash object
    hash_object = hashlib.md5(key_bytes)
    
    #Convert hash to hexadecimal string
    hash_hex = hash_object.hexdigest()
    
    return hash_hex


# Function for checking Database Cache
def get_cached_translation(text, source_lang, target_lang):
    '''
     Check if translation exists in database cache.
     RETURNS:
        str: Translated text if found in cache
        None: If not found in cache
    '''
    
    try:
        # find the translation in database
        cache_entry = TranslationCache.objects.get(
        original_text=text,
        source_language=source_lang,
        target_language=target_lang
        )
        
        # if found Return the cached translation
        return cache_entry.translated_text

    except TranslationCache.DoesNotExist:
        # Not found in cache
        return None
    
    
# Save to Database
def save_translation_cache(text, source_lang, target_lang, translated_text):
    '''
    Save new translation to database cache.
    
    '''
    # Create a new database record
    # .create() both creates and saves in one step
    TranslationCache.objects.create(
        original_text=text,
        source_language=source_lang,
        target_language=target_lang,
        translated_text=translated_text
    )

    print(f"  💾 Cached: '{text[:30]}...' ({source_lang}→{target_lang})")


