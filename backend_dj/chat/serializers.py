'''
Convert chat data between JSON and Python objects

    - Validates incoming chat requests from mobile app
    - Formats chat responses for mobile app
    - Converts ChatHistory model to JSON
'''

from rest_framework import serializers
from .models import ChatHistory


class ChatRequestSerializer(serializers.Serializer):
    '''
    Validates farmer's question from mobile app.
    Mobile app sends JSON
    '''
    # Farmer's question
    question = serializers.CharField(
        required = True,
        max_length = 500,
        help_text = "Farmer's question about crops, diseases, or farming"
    )
    
    # Number of chunks to retrieve
    top_k = serializers.IntegerField(
        required = False,
        default = 5,
        min_value = 1,
        max_value = 20,
        help_text = 'Number of relevant documents to retrieve'
    )
    
    
class SourceSerializer(serializers.Serializer):
    '''
    Formats source information for response.
    
    Shows farmer which PDF provided the answer.
    '''
    
    filename = serializers.CharField(help_text = 'PDF filename')
    page = serializers.CharField(help_text = 'Page number')
    relevance = serializers.FloatField(help_text = "Relevance score (0-1)")
    

class ChatResponseSerializer(serializers.Serializer):
    '''
    Formats the answer for mobile app.
    
    Mobile app receives JSON
    '''
    
    answer = serializers.CharField(help_text = 'Generated answer for farmer')
    source = SourceSerializer(many=True, help_text = 'Sources used for answer')
    success = serializers.BooleanField(help_text = 'Whether request succeeded')
    question = serializers.CharField(help_text = 'Original question')
    
    
class ChatHistorySerializer(serializers.ModelSerializer):
    '''
    Converts ChatHistory model to JSON for API responses.
    '''
    
    class Meta:
        model = ChatHistory
        fields = [
            'id', 'question', 'answer', 'sources', 'created_at'
        ]
        
        read_only_fields = ['id', 'created_at']
        
        
    
    
    
    