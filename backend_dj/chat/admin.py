from django.contrib import admin
from .models import ChatHistory

# Register your models here.

@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    """
    Admin configuration for ChatHistory model.
    Allows agronomists to view farmer questions and AI answers.
    """
    
    # Fields shown in the list view (full content, no slicing)
    list_display = (
        'id',
        'user',
        'question',
        'answer',
        'created_at'
    )
    
    # Clickable links
    list_display_links = ('id', 'user')
    
    # Searchable fields
    search_fields = ('user__phone_number', 'user__full_name', 'question', 'answer')
    
    # Filters on the right sidebar
    list_filter = ('created_at',)
    
    # Default sorting (newest first)
    ordering = ('-created_at',)
    
    # How many rows per page
    list_per_page = 25
    
    # Read-only fields (cannot edit)
    readonly_fields = ('created_at',)
    
    # Organize the edit page
    fieldsets = (
        ('Farmer Information', {
            'fields': ('user',)
        }),
        ('Chat Content', {
            'fields': ('question', 'answer', 'sources')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
