# predictions/urls.py - URL routing for prediction endpoints
from django.urls import path
from .views import PredictionView, HistoryView, PredictionDetailView

urlpatterns = [
    # POST /api/predict/ - Submit image and get prediction
    path('predict/', PredictionView.as_view(), name='predict'),
    # GET /api/history/ - Get user's prediction history
    path('history/', HistoryView.as_view(), name='history'),
    # GET /api/predict/<id>/ - Get details of a specific prediction
    path('predict/<int:pk>/', PredictionDetailView.as_view(), name='prediction-detail'),
]
