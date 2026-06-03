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

"""
URL configuration for betafarm project.
"""

from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from accounts.views import ProtectedTestView
from django.conf import settings
from django.conf.urls.static import static
from django.urls import re_path
from django.views.static import serve

# Remove the old home function - NO LONGER NEEDED
# def home(request):
#     return HttpResponse("BetaFarm AI API is running!")

urlpatterns = [
    # Frontend HTML Pages - ADD THESE
    path('', TemplateView.as_view(template_name='index.html'), name='index'),
    path('dashboard/', TemplateView.as_view(template_name='dashboard.html'), name='dashboard'),
    path('chat/', TemplateView.as_view(template_name='chat.html'), name='chat'),
    path('disease/', TemplateView.as_view(template_name='disease.html'), name='disease'),
    path('history/', TemplateView.as_view(template_name='history.html'), name='history'),
    path('profile/', TemplateView.as_view(template_name='profile.html'), name='profile'),
    path('otp/', TemplateView.as_view(template_name='otp.html'), name='otp'),
    
    # Django Admin Panel
    path("admin/", admin.site.urls), 
    
    # JWT AUTHENTICATION ENDPOINTS
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('api/protected/', ProtectedTestView.as_view(), name='protected_test'),
    
    # App URLs
    path('api/', include('accounts.urls')),
    path('api/', include('predictions.urls')),
    path('api/', include('translations.urls')),
    path('api/chat/', include('chat.urls')),
]

if settings.DEBUG:
    urlpatterns += [
        re_path(r'^css/(?P<path>.*)$', serve, {'document_root': BASE_DIR.parent / 'frontend/css'}),
        re_path(r'^js/(?P<path>.*)$', serve, {'document_root': BASE_DIR.parent / 'frontend/js'}),
    ]
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
