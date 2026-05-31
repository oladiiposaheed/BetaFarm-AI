"""
FILE: rag/routes/chat.py
PURPOSE: API endpoint for farmers to ask questions with session memory
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from llm.chat import farmer_chat

router = APIRouter(prefix="/api/v1", tags=["chat"])


class ChatRequest(BaseModel):
    """Request model for chat endpoint."""
    question: str = Field(..., description="Farmer's question")
    top_k: int = Field(5, description="Number of documents to retrieve", ge=1, le=20)
    session_id: Optional[str] = Field(None, description="Session ID for memory")


class SourceInfo(BaseModel):
    """Source information model."""
    filename: str
    page: str
    relevance: float


class ChatResponse(BaseModel):
    """Response model for chat endpoint."""
    answer: str
    sources: List[SourceInfo] = []


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Process farmer's question with session memory."""
    
    if not request.question or not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    # Pass session_id to maintain conversation memory
    result = farmer_chat.ask(
        question=request.question,
        session_id=request.session_id,
        top_k=request.top_k
    )
    
    sources = [
        SourceInfo(
            filename=s.get('filename', 'Unknown'),
            page=str(s.get('page', 'N/A')),
            relevance=s.get('relevance', 0.0)
        )
        for s in result.get('sources', [])
    ]
    
    return ChatResponse(
        answer=result.get('answer', 'No answer generated'),
        sources=sources
    )


@router.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}