from django.contrib import admin
from .models import TranslationCache
# Register your models here.

@admin.register(TranslationCache)
class TranslationCacheAdmin(admin.ModelAdmin):
    
    list_display = (
        'id', 'original_text_preview', 'source_language', 'target_language', 'created_at_formatted', 'last_accessed_formatted',
    )
    
    list_display_links = ('id', 'original_text_preview')
    list_filter = ('source_language', 'target_language', 'created_at',)
    search_fields = ('original_text', 'translated_text',)
    readonly_fields = ('created_at', 'last_accessed',)
    ordering = ('-created_at',)
    
    
    def original_text_preview(self, obj):
        if len(obj.original_text) > 50:
            return obj.original_text[:50] + '...'
        
        return obj.original_text
    
    # Set the column header name in admin panel
    original_text_preview.short_description = 'Original Text'
    
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%b %d, %Y - %I:%M %p')
    
    created_at_formatted.short_description = 'Created'
    
    
    def last_accessed_formatted(self, obj):
        return obj.last_accessed.strftime('%b %d, %Y - %I:%M %p')
    
    last_accessed_formatted.short_description = 'Last Used'