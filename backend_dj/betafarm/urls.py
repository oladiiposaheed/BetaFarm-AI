"""
URL configuration for betafarm project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from accounts.views import ProtectedTestView
from django.conf import settings
from django.conf.urls.static import static
from django.shortcuts import redirect

from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('', views.index_view, name='index'),  # Serve the main frontend page at the root URL
    path('', lambda request: redirect('/admin/', permanent=False)),
    # Django Admin Panel (agronomist dashboard)
    path("admin/", admin.site.urls), 
    
    # JWT AUTHENTICATION ENDPOINTS (for mobile app)
    
    # POST /api/token/ - Farmer sends phone + OTP → Gets tokens
    # Used when farmer logs in for the first time(Login: Get access + refresh tokens)
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    
    # POST /api/token/refresh/ - Farmer sends refresh token → Gets new access token
    # Used when access token expires (after 1 day)
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # POST /api/token/verify/ - Check if token is still valid
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    
    # GET /api/protected/: Test if JWT authentication is working
    path('api/protected/', ProtectedTestView.as_view(), name='protected_test'),
    
    # Account App URLs (OTP, login, signup)
    # OTP ENDPOINTS (from accounts app)
    # /api/auth/send-otp/ - Request OTP via SMS
    # Verify/Confirm OTP → get/receive JWT  OTP, receive JWT
    path('api/', include('accounts.urls')),
    
    # Prediction App URLs (disease prediction endpoints)
    path('api/', include('predictions.urls')),
    
    # Translations urls
    path('api/', include('translations.urls')),
    
    path('api/chat/', include('chat.urls')),
]

if settings.DEBUG:

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)