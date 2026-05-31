'''
Convert data to/from JSON
    - Validate incoming translation requests
    - Format outgoing translation responses
    - Convert TranslationCache model to JSON for admin
'''

from rest_framework import serializers
from .models import TranslationCache

#Create TranslationCacheSerializer
class TranslationCacheSerializer(serializers.ModelSerializer):
    '''
    Converts TranslationCache model to JSON format and not Python objects for admin panel and debugging.
    
    '''
    
    class Meta:
        model = TranslationCache
    
        fields = ['id', 'original_text', 'source_language', 'target_language', 'translated_text', 'created_at', 'last_accessed',]
    
    
# Create TranslateRequestSerializer
class TranslateRequestSerializer(serializers.Serializer):
    '''
    Validate incoming translation requests from mobile app.
    This prevents bad data from reaching our database.
    '''
    
    text = serializers.CharField(required=True, help_text="The text to translate (e.g., 'How to treat late blight?')") #required
    source_language = serializers.CharField(required=False, default='auto', help_text="Source language code for automatic detection, or 'en', 'yo', 'ha', etc.")
    target_language = serializers.CharField(required=True, help_text="Target language code (e.g., 'yo' for Yoruba, 'ha' for Hausa, 'ig' for Igbo)")
    
    def validate_target_language(self, value):
        '''
        Check if target language is supported.
        '''
        
        # List of supported languages
        supported_languages = ['en', 'yo', 'ha', 'ig', 'pcm', 'ar', 'fr']
        
        if value not in supported_languages:
            raise serializers.ValidationError(
                f"Unsupported language: '{value}'. Supported: {', '.join(supported_languages)}"
            )
             
        return value   
    
# Create TranslateResponseSerializer
class TranslateResponseSerializer(serializers.Serializer):
    '''
    Format the translation response, then send back to mobile app
    '''
    
    original_text = serializers.CharField(help_text='The original text that was requested for translation')
    translated_text = serializers.CharField(help_text='The translated text result')
    source_language = serializers.CharField(help_text='Detected or provided source language code')
    target_language = serializers.CharField(help_text='Target language code that was used')
    from_cache = serializers.BooleanField(help_text='True if response came from cache (instant), False if new translation')
    