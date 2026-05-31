'''
API endpoints for translation

PURPOSE:
    Handles translation requests from mobile app.
    
FLOW:
    1. Receive translation request
    2. Check cache for existing translation
    3. If found → return instantly (fast path)
    4. If not found → call RAG service (slow path)
    5. Save to cache for future requests
    6. Return translated text
'''

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.conf import settings
import requests
from .serializers import TranslateRequestSerializer, TranslateResponseSerializer
from .utils import get_cached_translation, save_translation_cache

# RAG Service URL
RAG_URL = getattr(settings, 'RAG_URL', 'http://localhost:8002')

class TranslateView(APIView):
    '''
    Translate text between languages.
    '''

    # Only authenticated users can translate
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        '''Handle POST request to translate text.'''
        
        # Validate the request
        serializer = TranslateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    
        # Extract validated data
        text = serializer.validated_data['text']
        source_lang = serializer.validated_data.get('source_language', 'en')
        target_lang = serializer.validated_data['target_language']
        
        # Check cache first (fast path)
        cached = get_cached_translation(text, source_lang, target_lang)

        if cached:
            # Return cached result instantly (50ms response)
            return Response({
                'original_text': text,
                'translated_text': cached,
                'source_language': source_lang,
                'target_language': target_lang,
                'from_cache': True
            })
            
        # Call RAG service
        try:
            response = request.post(
                f'{RAG_URL}/translate',
                json={
                    'text': text,
                    'source_language': source_lang,
                    'target_language': target_lang
                },
                timeout=30
            )
                
            if response.status_code == 200:
                translated_text = response.json().get('translated_text', text)
                    
            else:
                #return original text if translation fails
                translated_text = text
                    
            
        except Exception as e:
            # Network error or service unavailable
            translated_text = text
                                         
        #Save to cache for future requests
        return Response({
            'original_text': text,
            'translated_text': translated_text,
            'source_language': source_lang,
            'target_language': target_lang,
            'from_cache': False
        })                 