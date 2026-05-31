from fastapi import APIRouter
from datetime import datetime
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from llm.chat import farmer_chat
from retrieval.hybrid_search import hybrid_search
from retrieval.retriever import retriever
from vector_store.chroma_store import vector_db


# Create a router for health check endpoints
router = APIRouter(prefix='/api/v1', tags=['health'])

# Health check endpoint
@router.get('/health')
async def health_check():
    '''
    Check if RAG service is healthy and ready.
    
     URL: GET /api/v1/health
    
    Returns:
        - status: "healthy" or "unhealthy"
        - timestamp: Current time
        - vector_count: Number of vectors in database
        - chat_ready: Whether chat system is ready
    '''
    
    # Check if chat system is ready
    chat_ready = farmer_chat.is_ready if hasattr(farmer_chat, 'is_ready') else False
    
    # Check if search system is ready
    search_ready = hybrid_search.is_ready if hasattr(hybrid_search, 'is_ready') else False
    
    vector_count = vector_db.count() if vector_db else 0
    
    status = 'healthy' if (chat_ready and search_ready) else 'degraded'
        
    return {
        'status': status,
        'timestamp': datetime.now().isoformat(),
        'vector_count': vector_count,
        'chat_ready': chat_ready,
        'search_ready': search_ready,
        'service': 'BetaFarm AI - RAG Service'
    }
        

# Readiness Check endpoint (fro Kubernetes)

@router.get('/ready')
async def readiness_check():
    '''
    Check if service is ready to accept requests.
    
    URL: GET /api/v1/ready
    
    Returns 200 if ready, 503 if not ready.
    '''
    
    # Check if both chat and search are ready
    chat_ready = farmer_chat.is_ready if hasattr(farmer_chat, 'is_ready') else False
    search_ready = hybrid_search.is_ready if hasattr(hybrid_search, 'is_ready') else False
    
    if chat_ready and search_ready:
        return {'ready': True}
    
    else:
        return {
            'ready': False,
            'chat_ready': chat_ready,
            'search_ready': search_ready
        }
    
    
    
    