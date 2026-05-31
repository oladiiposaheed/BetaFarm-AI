from django.db import models
from django.conf import settings
# Create your models here.

'''                                              │

'''
# This model represents a single prediction made by the system
User = settings.AUTH_USER_MODEL

class Prediction(models.Model):
    
    '''
        Prediction model = Stores disease prediction results for each image uploaded by users.
        Every time a farmer uploads a new image, a new Prediction record is created with the results.
        Agronomists can also view these records to track the history of diagnoses for each user in the admin interface.
    '''
    
    # HEALTH STATUS CHOICES (for dropdown menu)
    HEALTH_STATUS_CHOICES = [
        ('healthy', 'Healthy'),
        ('unhealthy', 'Unhealthy'),
    ]
    
    # DATABASE FIELDS
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions', verbose_name='Farmer')
    image_url = models.CharField(max_length=255, verbose_name='Image URL', help_text='Path to the uploaded image file')
    # crop_name - What type of plant was detected (e.g., "Tomato", "Cassava")
    crop_name = models.CharField(max_length=100, verbose_name='Crop Name', help_text='Type of plant detected in the image')
    health_status = models.CharField(max_length=20, choices=HEALTH_STATUS_CHOICES, default='unhealthy', verbose_name='Health Status', help_text='Overall health status of the plant (Healthy or Unhealthy)')
    disease_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Disease Name', help_text='Name of the detected disease (or "Healthy")')
    # confidence - How sure the AI is (0.0 to 1.0)
    confidence = models.FloatField(default=0.0, verbose_name='Confidence Score', help_text='AI confidence score for the prediction (0.0 to 1.0)')
    solution = models.TextField(blank=True, null=True, verbose_name='Treatment Solution', help_text='Recommended treatment advice based on the detected disease from LLM/RAG')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At', help_text='Timestamp when the prediction was made')
    
    def __str__(self):
        
        return f'{self.user.full_name} {self.user.phone_number} - {self.disease_name} ({int(self.confidence * 100)}% confidence)'
    
    class Meta:
        ordering = ['-created_at']  # Newest predictions first
        # Human-readable name in admin panel
        verbose_name = 'Prediction'
        verbose_name_plural = 'Predictions'