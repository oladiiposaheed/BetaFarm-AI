from django.contrib import admin
from .models import Prediction
# Register your models here.

class PredictionAdmin(admin.ModelAdmin):
    '''
    Custom admin configuration for Prediction model.
    Controls what agronomists see when managing predictions.
    '''
    
    list_display = ('id', 'user', 'crop_name', 'disease_name', 'health_status', 'confidence_percent', 'created_at_short')
    list_display_links = ('id', 'user')
    search_fields = ('user__full_name', 'user__phone_number', 'crop_name', 'disease_name')
    list_filter = ('health_status', 'crop_name', 'created_at')

    list_per_page = 25
    
    ordering = ('-created_at',)  # Show newest predictions first

    
    # Organizes the edit page into sections
    fieldsets = (
        # Section 1: Farmer Information
        ('Farmer Information', {
            'fields': ('user',)
        }),
        
        
        # Section 2: Prediction Results
        ('Prediction Results', {
            'fields': ('image_url', 'crop_name', 'health_status', 'disease_name')
        }),
        
        # Section 3: Treatment Solution
        ('Treatment Solution', {
            'fields': ('solution',),
            'classes': ('wide',)  # Makes the solution field wider for better readability
        }),
        
        # Section 4: Metadata (read-only, collapsed by default)
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',),  # Collapses this section by default
        }),  
        
    )
    
    # ADD VIEW (when creating a NEW prediction)
    add_fieldsets = (
        (None, {
            'fields': ('user', 'image_url', 'crop_name', 'health_status', 'disease_name', 'confidence', 'solution'),
        }),
    )
    
    # READ-ONLY FIELDS
    readonly_fields = ('created_at',)
    
    
    
    # CUSTOM METHODS (for better display)
    def confidence_percent(self, obj):
        '''
        Converts confidence score to percentage for display in list view.
        
        Args:
            obj: The Prediction instance being displayed.
        '''
        return f'{int(obj.confidence * 100)}%'
    
    confidence_percent.short_description = 'Confidence (%)'  # Column header in admin list view
    confidence_percent.admin_order_field = 'confidence'  # Allows sorting by confidence score

    def created_at_short(self, obj):
        '''
        Displays a shortened version of the created_at timestamp for better readability in list view.
        
        Args:
                obj: The Prediction object
                
            Returns:
                str: Formatted date and time
        '''
        return obj.created_at.strftime('%Y-%m-%d %H:%M')

    created_at_short.short_description = 'Created At'  # Column header in admin list view
    created_at_short.admin_order_field = 'created_at'  # Allows sorting by created_at timestamp
    
admin.site.register(Prediction, PredictionAdmin)
