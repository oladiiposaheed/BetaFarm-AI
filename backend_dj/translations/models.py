from django.db import models

# Create your models here.


'''
    Translation Cache Database Model
    This model stores translated text in the database to avoid repeated API calls. 
'''

class TranslationCache(models.Model):
    original_text = models.TextField(help_text="The original text to translate (e.g., 'How to treat late blight?')")
    source_language = models.CharField(max_length=10, help_text="Language code of original text (e.g., 'en' for English, 'yo' for Yoruba)")
    target_language = models.CharField(max_length=10, help_text="Language code to translate to (e.g., 'yo', 'ha', 'ig', 'pcm', 'ar', 'fr')")
    translated_text = models.TextField(help_text='The chched translated text result')
    created_at = models.DateTimeField(auto_now_add=True, help_text='When this translation was first cached')
    last_accessed = models.DateTimeField(auto_now=True, help_text='When this translation was last accessed (for cache cleanup)')
    
    class Meta:
        # Prevent duplicate translations
        unique_together = ('original_text', 'source_language', 'target_language')
        
        indexes = [
            models.Index(fields=['source_language', 'target_language'])
        ]
        
        verbose_name = 'Translation Cache'
        verbose_name_plural = 'Translation Caches'
        
        def __str__(self):
            preview = self.original_text[:50]
            
            if len(self.original_text) > 50:
                preview += '...'
            
            return f'{preview} ({self.source_language} -> {self.target_language})'