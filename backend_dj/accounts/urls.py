'''
URL routing for authentication endpoints
'''

from django.urls import path
from .views import SendOTPView, VerifyOTPView, ProtectedTestView

urlpatterns = [
    # POST /api/auth/send-otp/ - Request 6-digit code via SMS: send otp
    path('auth/send-otp/', SendOTPView.as_view(), name='send_otp'),
    
    # POST /api/auth/verify-otp/ - Confirm code, receive JWT tokens
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    
    # GET /api/auth/protected/ - Test endpoint (requires valid JWT)
    path('auth/protected/', ProtectedTestView.as_view(), name='protected_test'),
]

