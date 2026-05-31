'''
 FastAPI application entry point
 This file:
    1. Creates the FastAPI app
    2. Adds CORS middleware (allows Django to call this API)
    3. Includes all routes (predict, health)
    4. Starts the server when run directly
 
'''

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import predict, health
from config import HOST, PORT

# Create FastAPI app
app = FastAPI(
    title='BetaFarm AI - Disease Detection API',
    description='ML inference API for plant disease detection',
    version='1.0.0'
)

# Add CORS middleware (allow Django to call this API)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'], # Allow all origins (for development)
    allow_credentials=True,
    allow_methods=['*'], # Allow all HTTP methods (GET, POST, etc.)
    allow_headers=['*']
)

# Include routes
app.include_router(predict.router, tags=['Prediction'])
app.include_router(health.router, tags=['Health'])

@app.get('/')
async def root():
    # result = {
    #     'message': 'BetaFarm AI Disease Detection API',
    #     'status': 'running',
    #     'endpoints': [
    #         '/predict (POST) - Send image for disease detection',
    #         '/health (GET) - Check API health'
    #     ]
    # }
    
    # return result
    return {
        'message': 'BetaFarm AI API is running',
        'status': 'online'
    }
    
if __name__=='__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8001)