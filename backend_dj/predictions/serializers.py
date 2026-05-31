from .models import Prediction
from rest_framework import serializers

#READ - Send data tO mobile app from the database in JSON format
class PredictionSerializer(serializers.ModelSerializer):
    ''''
    Serializer for the Prediction model.
    This converts Prediction model instances into JSON format for API responses.
    It also validates incoming data when creating or updating predictions via the API.
    '''
    
    class Meta:
        # The model we are serializing
        model = Prediction
        
        # List all the fields to send to the mobile app in JSON format
        fields = ['id', 'image_url', 'crop_name', 'health_status', 'disease_name', 'confidence', 'solution', 'created_at']
        
        
# CREATE - Receive data FROM mobile app        
class PredictionCreateSerializer(serializers.ModelSerializer):
    '''
    Serializer for creating new Prediction instances.
    This is used when the mobile app sends data to create a new prediction or image record.
    It includes validation to ensure the incoming data is correct before saving to the database.
    '''
    
    class Meta:
        model = Prediction
        # Fields that the mobile app will send when creating a new prediction.
        fields = ['user', 'image_url', 'crop_name', 'health_status', 'disease_name', 'confidence', 'solution']