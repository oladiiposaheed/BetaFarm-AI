'''
Health Check Endpoint

PURPOSE:
    Provides a simple endpoint to check if the API server is running.
    Used by monitoring tools and Django to verify service availability.
'''

from fastapi import APIRouter

# Create router
router = APIRouter()

@router.get('/health')
async def health_check():
    '''
    Health check endpoint.
    
    USAGE:
        GET /health
    
    RETURNS:
        {
            "status": "healthy",
            "service": "BetaFarm AI - Disease Detection API"
        }
    '''
    
    return {
        'status': 'healthy',
        'service': 'BetaFarm AI - Disease Detection API',
        'model_loaded': True # Can be extended to check model status
    }
    