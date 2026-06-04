'''
Utils for OTP generation and SMS sending
'''

import random
from datetime import timedelta
from django.utils import timezone
from .models import OTP
from django.conf import settings
import africastalking

try:
    AFRICASTALKING_AVAILABLE = True
    
except ImportError:
    AFRICASTALKING_AVAILABLE = False
    print('africastalking not installed. Run: pip install africastalking')
    
def generate_otp(phone_number):
    '''
    Generate a 6-digit OTP code and save it to the database.
    '''
    
    # Delete any existing UNUSED OTPs for this phone number
    OTP.objects.filter(
        phone_number=phone_number,
        is_used=False,
        expires_at__gt=timezone.now()
    ).delete()
    
    # Generate a random 6-digit number
    otp_code = str(random.randint(100000, 999999))
    
    # Calculate expiry time (10 minutes from now)
    expire_at = timezone.now() + timedelta(minutes=10)
    
    # Save the OTP to the database
    OTP.objects.create(
        phone_number=phone_number,
        otp_code=otp_code,
        expires_at=expire_at,
        is_used=False
    )
    
    return otp_code


def send_sms_africastalking(phone_number, message):
    '''
    Send SMS using Africa's Talking
    '''
    
    if not AFRICASTALKING_AVAILABLE:
        print('africastalking package not installed')
        return False

    try:
        # Get credentials from settings
        username = getattr(settings, 'AFRICASTALKING_USERNAME', 'sandbox')
        api_key = getattr(settings, 'AFRICASTALKING_API_KEY', '')
        
        if not api_key:
            print('AFRICASTALKING_API_KEY not set in environment variables')
            return False    
        
        # Initialize Africa's Talking
        africastalking.initialize(username, api_key)
        sms = africastalking.SMS
        
        # Format phone number (ensure it starts with 234)
        # Remove any + or 0 prefix
        phone_number = phone_number.strip()
        
        if phone_number.startswith('+'):
            phone_number = phone_number[1:]
            
        elif phone_number.startswith('0'):
            phone_number = '234' + phone_number[1:]
            
        elif not phone_number.startswith('234'):
            phone_number = '234' + phone_number
        
        # Get sender ID from settings
        sender = getattr(settings, 'AFRICASTALKING_SENDER', 'BetaFarm')
        print(f'📱 Sending SMS to {phone_number}')
        print(f'Message: {message}')
        
        # Send SMS
        response = sms.send(message, [phone_number], sender_id=sender)
        
        print('SME sent successfully!')
        print(f'   Response: {response}')
        return True
    
    except Exception as e:
        print(f"Africa's Talking SMS failed: {e}")
        return False
    

def send_sms_console(phone_number, message):
    '''
    Fallback SMS sender that just prints to console
    '''
    print(f"\n{'='*50}")
    print(f"📱 SMS TO {phone_number}")
    print(f"   {message}")
    print(f"{'='*50}\n")
    return True


def send_otp_via_sms(phone_number):
    '''
    Generate OTP and send it via SMS to the farmer.
    Uses Africa's Talking.
    '''
    
    # Generate a new 6-digit OTP code
    otp_code = generate_otp(phone_number)
    
    # Create the SMS message
    message = f'Your BetaFarm AI verification code is: {otp_code}. It expires in 10 minutes.'
    
    # Send via Africa's Talking
    sent = send_sms_africastalking(phone_number, message)
    
    # If SMS fails, print to console 
    if not sent:
        send_sms_console(phone_number, message)
    
    return True


def verify_otp(phone_number, code):
    """
    Verify if the provided OTP code is correct and not expired.
    """
    
    print(f"Verifying OTP for {phone_number} with code: {code}")
    
    try:
        # Find the OTP in database
        otp_record = OTP.objects.get(
            phone_number=phone_number,
            otp_code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        )
        
        print(f"Found valid OTP record: {otp_record.otp_code}")
        
        # Mark this OTP as used
        otp_record.is_used = True
        otp_record.save()
        
        print(f"OTP verified and marked as used")
        return True
        
    except OTP.DoesNotExist:
        print(f"No valid OTP found for {phone_number} with code {code}")
        return False    
    