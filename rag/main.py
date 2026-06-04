from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import chat, health
import uvicorn
import os

app = FastAPI(title='BetaFarm AI - RAG Service')

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

app.include_router(chat.router)
app.include_router(health.router)

@app.get('/')
async def root():
    return {
        "service": "BetaFarm AI - RAG Service",
        "status": "running",
        "endpoints": {
            "chat": "POST /api/v1/chat",
            "health": "GET /health"
        }
    }

@app.get('/health')
async def health_check():
    return {"status": "healthy", "service": "RAG Service"}

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8002))
    uvicorn.run(app, host='0.0.0.0', port=port)