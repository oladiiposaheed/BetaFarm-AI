'''
    Custom JWT serializer to use phone_number instead of username
    Converts User model to JSON
'''

#from django.contrib.auth import get_user_model
from rest_framework import serializers
#from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User

class UserSerializer(serializers.ModelSerializer):
    
    '''
    Serializer for User model.
    Converts User objects to JSON format for API responses.
    '''
    
    class Meta:
        # Tell Django which model to serialize
        model = User
        
        # Which fields to include in JSON response
        fields = [
            'id', 
            'phone_number',
            'full_name',
            'preferred_language', 
            'is_agronomist', 
            'voice_enabled', 
            'created_at'
        ]
        
        #Unchanged Fields
        read_only_filess = ['id', 'created_at'] 


