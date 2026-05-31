from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
# Register your models here.


class UserAdmin(BaseUserAdmin):
    '''
    Custom admin configuration for User model.
    Controls what agronomists see when managing farmers in admin panel.
    '''
    
    # Fields shown in the user list page (table view)
    list_display = (
        'phone_number', 'full_name', 'preferred_language', 'is_agronomist', 'voice_enabled', 'created_at',
    )
    
    # Fields that can be clicked to sort the table
    list_display_links = ('phone_number', 'full_name')
    
    # Fields that can be searched (adds a search bar)
    search_fields = ('phone_number', 'full_name')
    
    # Filters on the right sidebar
    list_filter = ('is_agronomist', 'preferred_language', 'voice_enabled', 'created_at')
    
    # How many rows to show per page
    list_per_page = 25
    
    # Sort users by phone_number
    ordering = ('phone_number',)
    
    fieldsets = (
        # Section 1: Personal Information
        ('Personal Information', {
            'fields': ('phone_number', 'full_name', 'preferred_language')
        }),
        
        # Section 2: Settings
        ('Settings', {
            'fields': ('voice_enabled', 'is_agronomist')
        }),
        
        # Section 3: Metadata (collapsed by default)
        ('Metadata', {
            'fields': ('created_at', 'last_login', 'date_joined'),
            'classes': ('collapse',)  # Hidden until you click "▼"
        }),
    )
    
    # Fields shown when creating a new user (add user page)
    add_fieldsets = (
         (None, {
             'classes': ('wide',),
             'fields': ('phone_number', 'full_name', 'preferred_language', 'voice_enabled', 'is_agronomist', 'password1', 'password2'),
         }),
     )
    
    # Make phone_number read-only after creation (cannot change)
    readonly_fields = ('created_at', 'last_login', 'date_joined') 
    
admin.site.register(User, UserAdmin)