from django.shortcuts import render
from rest_framework.views import APIView # Allows us to create class-based API views
from rest_framework.response import Response # Returns HTTP responses (JSON format)
from rest_framework.permissions import IsAuthenticated # Restricts access to authenticated users only
from rest_framework_simplejwt.views import TokenObtainPairView # Built-in view that generates JWT tokens, we will use this for login
from .serializers import UserSerializer # Converts User model to JSON format (will create next)
from rest_framework import status
from .models import User
from .utils import send_otp_via_sms, verify_otp
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from .serializers import UserSerializer

# Create your views here.

#API endpoints for user authentication

# PROTECTED TEST VIEW (for testing JWT authentication)

class ProtectedTestView(APIView):
    '''
        Test endpoint to verify JWT authentication is working.
        Only accessible if user provides a valid JWT token.
        
        URL: GET /api/protected/
        Headers: Authorization: Bearer <access_token>
    '''
    #Only allow access if user is authenticated (has valid token), without this, anybody could access this endpoint
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        '''
            Handle GET requests to this endpoint.
        
            Args:
                request: The HTTP request object (contains user info if authenticated)
                
            Returns:
                Response: JSON message confirming user is authenticated
        '''
        
        # Get authenticated user(farmer) from JWT token
        user = request.user
        
        # Return a success message with user's phone number
        # This proves the token worked and we know who they are
        
        return Response({
            'message': 'You are authenticated! JWT is working!',
            'phone_number': user.phone_number, # Show which user is logged in
            'full_name': user.full_name # Show user's name
        })
        
        
class SendOTPView(APIView):
    '''
    API endpoint: for sending OTP to farmer's phone number.
    URL: POST /api/auth/send-otp/
    This endpoint is PUBLIC (no authentication needed)
    '''
    
    # NO authentication required - anyone can request OTP
    
    authentication_classes = [] # Disable JWT
    permission_classes = [] # Allow anyone
    def post(self, request):
        
        # Step 1: Get phone number from request body
        phone_number = request.data.get('phone_number')
        
        # Step 2: Validate - phone number is required
        if not phone_number:
            return Response(
                {'error': 'Phone number is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Step 3: Send OTP via SMS
        send_otp_via_sms(phone_number)
        
        # Step 4: Return success response
        return Response(
            {'message': 'OTP sent successfully'},
            status=status.HTTP_200_OK
        )
        
        
class VerifyOTPView(APIView):
    '''
    API endpoint: for verifying OTP and logging in.
    
    URL: POST /api/auth/verify-otp/
    
    This endpoint is PUBLIC (no authentication needed)
    '''
    
     # NO authentication required - anyone can verify OTP
    authentication_classes = []  # Disable JWT
    permission_classes = []      # Allow anyone
    def post(Self, request):
        
        # Step 1: Get phone number and OTP code from request
        phone_number = request.data.get('phone_number')
        otp_code = request.data.get('otp_code')
        
        # Step 2: Validate - both fields are required
        if not phone_number or not otp_code:
            response = Response(
                {'error': 'Phone number and OTP code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
            return response
        
        # Step 3: Verify the OTP code
        is_valid = verify_otp(phone_number, otp_code)
        
        # Step 4: If invalid, return error
        if not is_valid:
            response = Response(
                {'error': 'Invalid or expired OTP code'},
                status=status.HTTP_400_BAD_REQUEST
            )
            return response
            
        # Step 5: Get or create user
        # If user exists, get them. If not, create new farmer account
        
        user, created = User.objects.get_or_create(
            phone_number=phone_number,
            defaults={
                'full_name': f'Farmer_{phone_number[-6:]}', # Temporary name
                'preferred_language': 'en',
                'voice_enabled': True
            }    
        )
        
        # Step 6: Generate JWT tokens for the user
        refresh = RefreshToken.for_user(user)
        
        # Step 7: Return tokens + user info
        response = Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        }, status=status.HTTP_200_OK)
        
        return response
    
    
    
        
        
        