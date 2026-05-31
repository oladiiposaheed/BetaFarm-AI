from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager

# Create your models here.

class UserManager(BaseUserManager):
    '''
        Custom manager for User model without username field
    '''
    
    def create_user(self, phone_number, full_name, password=None, **extra_fields):
        '''
        Create and save a regular farmer user
        '''
        
        if not phone_number:
            raise ValueError('Phone number is required')
        
        if not full_name:
            raise ValueError('Full name is required')
        
        user = self.model(
            phone_number=phone_number,
            full_name=full_name,
            **extra_fields
        )
        user.set_password(password)
        user.save(using=self._db)
        return user
    
    def create_superuser(self, phone_number, full_name, password=None, **extra_fields):
        '''
            Create and save a superuser (agronomist/admin) user
        '''
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        return self.create_user(phone_number, full_name, password, **extra_fields)
    

class User(AbstractUser):
    '''
        Custom User model using phone number for login instead of username.
        Farmers log in with phone number + OTP.
    '''
     # Remove username field (we don't need it)
    username = None
    
    # Supported language choices for multilingual UI
    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('yo', 'Yoruba'),
        ('ha', 'Hausa'),
        ('ig', 'Igbo'),
        ('pe', 'Pidgin English'),
        ('ar', 'Arabic'),
        ('fr', 'French'),
    ]
    
    # Core user fields
    phone_number = models.CharField(max_length=15, unique=True, blank=False, null=False, verbose_name='Phone Number')
    full_name = models.CharField(max_length=120, null=False, blank=False, verbose_name='Full Name')
    preferred_language = models.CharField(max_length=30, default='en', choices=LANGUAGE_CHOICES, verbose_name='Preferred Language')
    voice_enabled = models.BooleanField(default=True, verbose_name='Voice Enabled', help_text='Enable voice reponses for questions')
    is_agronomist = models.BooleanField(default=False, verbose_name='Is Agronomist', help_text='Expert user(agronomist) who can access web dashboard and review disease predictions?')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')

    # Use our custom manager
    objects = UserManager()

    # Tell Django to use phone_number login login instead of default(username)
    USERNAME_FIELD = 'phone_number'

    # Ask for full_name when creating superuser besides phone_number
    REQUIRED_FIELDS = ['full_name']

    def __str__(self):
        return f'{self.full_name} - ({self.phone_number})'
    
    # HELPER METHODS (for convenience)
    def get_language_display_name(self):
        '''
            Convert language code ('en') to full name ('English')
            Used in templates and API responses
        '''
        
        language_dict = {
            'en': 'English',
            'yo': 'Yoruba',
            'ha': 'Hausa',
            'ig': 'Igbo',
            'pcm': 'Pidgin English',
            'ar': 'Arabic',
            'fr': 'French',
        }
        
        return language_dict.get(self.preferred_language, 'English')


# OTP MODEL - Stores temporary verification codes
class OTP(models.Model):
    '''
        Stores OTP codes temporarily for phone verification.
        Codes expire after 5 minutes for security.
    '''

    phone_number = models.CharField(max_length=15, help_text="Farmer's phone number receiving this # Core user fields(OTP)")
    otp_code = models.CharField(max_length=6, help_text='6-digit one-time password')
    expires_at = models.DateTimeField(help_text='Time when this OTP expires and cannot be used.')
    is_used = models.BooleanField(default=False, help_text='True if this code has already been verified') # Whether this OTP has already been used
    created_at = models.DateTimeField(auto_now_add=True, help_text='Time when this OTP code was generated')
    
    
    def is_valid(self):
        '''
        Check if OTP is still valid (not expired and not used).
        
        A code is valid if:
        1. NOT already used (is_used = False)
        2. NOT expired (expires_at > current time)
        
        Returns:
            True if OTP can be used, False otherwise
        '''
        
        # Check: Not used(True) AND not expired(True)
        from django.utils import timezone
        
        return not self.is_used and self.expires_at > timezone.now()
    
    def __str__(self):
        return f'{self.phone_number} - {self.otp_code}'
    
        
        
