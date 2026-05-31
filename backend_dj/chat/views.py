"""
FILE: backend_dj/chat/views.py
PURPOSE: API endpoints for farmer chat with session memory
"""

import requests
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.conf import settings
from django.core.paginator import Paginator
from .models import ChatHistory


class ChatView(APIView):
    """API endpoint for farmer to ask questions."""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Process farmer's question and return answer."""
        
        question = request.data.get('question')
        top_k = request.data.get('top_k', 5)
        session_id = request.data.get('session_id', str(request.user.id))
        
        if not question:
            return Response({'error': 'Question required'}, status=status.HTTP_400_BAD_REQUEST)
        
        rag_url = getattr(settings, 'RAG_SERVICE_URL', 'http://localhost:8002')
        
        try:
            # Pass session_id to RAG service for memory
            response = requests.post(
                f'{rag_url}/api/v1/chat',
                json={
                    'question': question,
                    'top_k': top_k,
                    'session_id': session_id
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                answer = data.get('answer', '')
                sources = data.get('sources', [])
                
                # Save to database
                ChatHistory.objects.create(
                    user=request.user,
                    question=question,
                    answer=answer,
                    sources=sources
                )
                
                return Response({
                    'answer': answer,
                    'sources': sources
                })
            else:
                return Response({'error': 'RAG service error'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except requests.exceptions.Timeout:
            return Response({'error': 'Request timed out'}, status=status.HTTP_504_GATEWAY_TIMEOUT)
        except requests.exceptions.ConnectionError:
            return Response({'error': 'RAG service unavailable'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChatHistoryView(APIView):
    """API endpoint for farmer to view past questions."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Return farmer's chat history."""
        
        chats = ChatHistory.objects.filter(user=request.user).order_by('-created_at')
        page = request.GET.get('page', 1)
        paginator = Paginator(chats, 10)
        
        try:
            page_obj = paginator.page(page)
        except:
            return Response({'error': 'Page not found'}, status=status.HTTP_404_NOT_FOUND)
        
        data = []
        for chat in page_obj:
            data.append({
                'id': chat.id,
                'question': chat.question,
                'answer': chat.answer[:200],
                'created_at': chat.created_at.isoformat()
            })
        
        return Response({
            'count': paginator.count,
            'total_pages': paginator.num_pages,
            'current_page': page,
            'results': data
        })


class ChatDetailView(APIView):
    """API endpoint for single chat operations."""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request, pk):
        """Get specific chat."""
        try:
            chat = ChatHistory.objects.get(id=pk, user=request.user)
            return Response({
                'id': chat.id,
                'question': chat.question,
                'answer': chat.answer,
                'sources': chat.sources,
                'created_at': chat.created_at.isoformat()
            })
        except ChatHistory.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)
    
    def delete(self, request, pk):
        """Delete specific chat."""
        try:
            chat = ChatHistory.objects.get(id=pk, user=request.user)
            chat.delete()
            return Response({'message': 'Chat deleted successfully'})
        except ChatHistory.DoesNotExist:
            return Response({'error': 'Chat not found'}, status=status.HTTP_404_NOT_FOUND)