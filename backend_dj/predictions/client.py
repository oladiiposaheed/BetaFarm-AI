# predictions/client.py - Django → FastAPI bridge for disease predictions

import requests
from django.conf import settings
import logging
import time

logger = logging.getLogger(__name__)

FASTAPI_URL = getattr(settings, 'FASTAPI_URL', 'http://localhost:8001')


def call_fastapi_predict_sync(image_bytes):
    """
    Send image bytes to FastAPI, return prediction dict.
    """
    
    max_retries = 3
    retry_delay = 2  # Increased from 1 to 2 seconds
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f'Attempt {attempt} to call FastAPI')
            
            files = {'image': ('image.jpg', image_bytes, 'image/jpeg')}
            
            # Use correct URL (no trailing slash)
            response = requests.post(
                f'{FASTAPI_URL}/predict',  # No trailing slash
                files=files,
                timeout=60  # Increased from 30 to 60 seconds
            )

            if response.status_code == 200:
                logger.info(f'Prediction successful')
                return response.json()
            else:
                logger.warning(f'FastAPI returned {response.status_code}')
                    
        except requests.exceptions.Timeout:
            logger.error(f'Attempt {attempt} timed out')
        except requests.exceptions.ConnectionError as e:
            logger.error(f'Attempt {attempt} connection error: {e}')
        except Exception as e:
            logger.error(f'Attempt {attempt} failed: {e}')
        
        if attempt < max_retries:
            time.sleep(retry_delay)
    
    raise Exception('FastAPI unavailable after 3 attempts')