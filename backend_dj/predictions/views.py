from django.shortcuts import render
import os
import uuid
import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.conf import settings
from django.core.files.base import ContentFile
from .models import Prediction
from .serializers import PredictionSerializer, PredictionCreateSerializer
from .client import call_fastapi_predict_sync

# Create your views here.

'''
# predictions/views.py - API endpoints for disease predictions
This file defines the API views that handle requests from the mobile app for disease predictions.
It uses Django REST Framework to create API endpoints that allow the mobile app to:
1. Send an image for prediction (POST /api/predictions/)
2. Retrieve past predictions (GET /api/predictions/)
The views interact with the Prediction model and use serializers to convert data to/from JSON format.
The main view is PredictionViewSet, which provides both list and create actions for predictions.
'''

# PAGINATION (splits history into pages)
class PredictionPagination(PageNumberPagination):
    '''Show 10 predictions per page in the history endpoint'''
    
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50
    
# VIEW 1: CREATE PREDICTION (POST /api/predict/)
class PredictionView(APIView):
    '''
    Submit an image and get disease prediction.
    
    POST: /api/predict/
    Body: form-data with 'image' file field
    '''
    
    # Only authenticated users can access this endpoint
    permission_classes = [IsAuthenticated]
    
    def _get_treatment_from_rag(self, disease_name: str) -> str:
        """Get treatment solution from RAG service for the detected disease."""
        
        if not disease_name or disease_name == 'Unknown':
            return 'No treatment information available for unknown disease.'
        
        try:
            rag_url = getattr(settings, 'RAG_SERVICE_URL', 'http://localhost:8002')
            
            # Ask RAG about treatment for this specific disease
            response = requests.post(
                f'{rag_url}/api/v1/chat',
                json={
                    'question': f'How to treat {disease_name}? Please provide practical steps.',
                    'top_k': 5,
                    'session_id': None
                },
                timeout=30
            )
            
            if response.status_code == 200:
                answer = response.json().get('answer', '')
                # Clean up the answer (remove reasoning if present)
                if 'FINAL ANSWER:' in answer:
                    answer = answer.split('FINAL ANSWER:')[-1].strip()
                elif 'ANSWER:' in answer:
                    answer = answer.split('ANSWER:')[-1].strip()
                return answer
            else:
                return f'Treatment information temporarily unavailable.'
                
        except requests.exceptions.Timeout:
            return 'Treatment request timed out. Please try again.'
        except requests.exceptions.ConnectionError:
            return 'Treatment service unavailable. Please try again later.'
        except Exception as e:
            return f'Error getting treatment: {str(e)[:100]}'
    
    def post(self, request):
        '''
        1. Receive/get uploaded image from mobile app
        2. Validate that an image was uploaded
        3. Read image as bytes
        4. Call FastAPI to get prediction results
        5. Get treatment from RAG service
        6. Save prediction to database
        7. Return JSON response to mobile app
        '''
        
        # Step 1: Get the uploaded image from the request from the mobile app (form-data)
        uploaded_file = request.FILES.get('image')
        
        # Step 2: Validate that an image was uploaded
        if not uploaded_file:
            return Response(
                {'error': 'No image file provided. Please upload an image.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Step 3: Read the image as bytes
        image_bytes = uploaded_file.read()
        
        # Step 4: Call FastAPI to get prediction results
        try:
            prediction_result = call_fastapi_predict_sync(image_bytes)
        
        except Exception as e:
            return Response(
                {'error': f'AI service is currently unavailable. Please try again later. Details: {str(e)}'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Get disease name from prediction
        disease_name = prediction_result.get('disease_name', 'Unknown')
        
        # Step 5: Get treatment from RAG service
        solution = self._get_treatment_from_rag(disease_name)
        
        # Step 6: Save image to media folder 
        unique_filename = f'predictions/{request.user.id}_{uuid.uuid4().hex[:8]}.jpg'
        filepath = os.path.join(settings.MEDIA_ROOT, unique_filename)
        
        # Create the directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # Write the image bytes to the file
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        # Step 7: Create prediction record in database
        prediction = Prediction.objects.create(
            user=request.user,
            image_url=f'{settings.MEDIA_URL}{unique_filename}',
            crop_name=prediction_result.get('crop_name', 'Unknown'),
            health_status=prediction_result.get('health_status', 'Unhealthy'),
            disease_name=disease_name,
            confidence=prediction_result.get('confidence', 0.0),
            solution=solution
        )
        
        # Step 8: Return JSON response to mobile app with the prediction results
        serializer = PredictionSerializer(prediction)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    
# VIEW 2: GET PREDICTION HISTORY (GET /api/history/)

class HistoryView(APIView):
    ''''
    Get user's past predictions (history).
    
    GET: /api/history/?page=1
    '''
    
    # Allow only authenticated users to access this endpoint
    permission_classes = [IsAuthenticated] 
    
    def get(self, request):
        ''''
        1. Get all predictions for this user from the database, newest first
        2. Paginate the results (10 per page)
        3. Serialize the data and return in JSON format
        '''
        
        predictions = Prediction.objects.filter(user=request.user).order_by('-created_at')
        
        # Step 2: Paginate the results
        paginator = PredictionPagination()
        paginated_predictions = paginator.paginate_queryset(predictions, request)
        
        # Step 3: Serialize the data and return in JSON format
        serializer = PredictionSerializer(paginated_predictions, many=True)
        
        return paginator.get_paginated_response(serializer.data)
    
    
# VIEW 3: PREDICTION DETAIL (GET /api/predict/<id>/)
class PredictionDetailView(APIView):
    ''''
    1. Get details of a specific prediction by ID.
    GET: /api/predict/<id>/
    2. Check if user is the owner of the prediction before returning details (security).
    3. Return the prediction details in JSON format.
    '''
    
    # Only authenticated users can access this endpoint
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        try:
            # Get the prediction by ID, ensure it belongs to the requesting user
            prediction = Prediction.objects.get(id=pk)
        
        except Prediction.DoesNotExist:
            return Response(
                {'error': 'Prediction not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
            
        # Check if the prediction belongs to the requesting user
        if prediction.user != request.user:
            return Response(
                {'error': 'You do not have permission to view this prediction.'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Serialize the prediction details and return in JSON format
        serializer = PredictionSerializer(prediction)
        return Response(serializer.data, status=status.HTTP_200_OK)