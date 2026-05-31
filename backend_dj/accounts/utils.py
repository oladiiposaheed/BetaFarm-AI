''' ---  Add OTP Generation Function  ---'''

#Helper functions for OTP and SMS
import random
import pyotp
from django.utils import timezone
from datetime import timedelta
from .models import OTP


def generate_otp(phone_number):
    '''
    Generate a 6-digit OTP code and save it to the database.
    
    What this does:
    1. Creates a random 6-digit number (e.g., 482039)
    2. Saves it to the OTP table with expiry time (5 minutes from now)
    3. Deletes any old/unused OTPs for this phone number
    
    Args:
        phone_number: The farmer's phone number (e.g., "08012345678")
    
    Returns:
        The 6-digit OTP code as a string (e.g., "482039")
    '''
    
    # Delete any existing UNUSED OTPs for this phone number to prevent multiple valid codes for the same number
    OTP.objects.filter(
        phone_number=phone_number,
        is_used=False,
        expires_at__gt=timezone.now() # Only delete valid ones
    ).delete()
    
    # Generate a random 6-digit number (100000 to 999999)
    otp_code = str(random.randint(100000, 999999))
    
    # Calculate expiry time (5 minutes from now)
    expires_at = timezone.now() + timedelta(minutes=10)
    
    # Save the OTP to database
    OTP.objects.create(
        phone_number=phone_number,
        otp_code=otp_code,
        expires_at=expires_at,
        is_used=False
    )
    
    return otp_code


def send_sms(phone_number, message):
    '''
    Send SMS to farmer's phone number.
    
    Prints to console (for testing)
    
    Args:
        phone_number: Where to send the SMS
        message: The text message to send
    '''
    print(f'\n📱 SMS TO {phone_number}')
    print(f'   {message}\n')
    
    
def send_otp_via_sms(phone_number):
    '''
    Generate OTP and send it via SMS to the farmer.
    
    This is the MAIN function called by the API endpoint.
    
    Args:
        phone_number: The farmer's phone number
    
    Returns:
        True if OTP was sent successfully, False otherwise
    '''
    
    # Generate a new 6-digit OTP code
    otp_code = generate_otp(phone_number)
    
    # Create the SMS message (in English for now)
    message = f'Your BetaFarm AI verification code is: {otp_code}. Valid for 5 minutes.'
    
    # Send the SMS
    send_sms(phone_number, message)
    
    return True


def verify_otp(phone_number, code):
    '''
    Verify if the provided OTP code is correct and not expired.
    
    Args:
        phone_number: The farmer's phone number
        code: The 6-digit code entered by farmer
    
    Returns:
        True if code is valid, False otherwise
    '''
    
    try:
        # Find the OTP in database:
        # - Must match phone_number
        # - Must match code
        # - Must NOT be used (is_used=False)
        # - Must NOT be expired (expires_at > now)
        otp_record = OTP.objects.get(
            phone_number=phone_number,
            otp_code=code,
            is_used=False,
            expires_at__gt=timezone.now()
        )
    
        # Mark this OTP as used so it cannot be reused
        otp_record.is_used = True
        otp_record.save()
        
        return True
    
    except OTP.DoesNotExist:
        # No matching OTP found - invalid code
        return False
    