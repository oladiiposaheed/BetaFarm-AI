from django.urls import path
from .views import ChatView, ChatHistoryView, ChatDetailView

urlpatterns = [
    path('ask/', ChatView.as_view(), name='chat_ask'), # POST /api/chat/ask/ - Ask a question
    path('history/', ChatHistoryView.as_view(), name='chat_history'),  # GET: Get chat history
    path('history/<int:pk>/', ChatDetailView.as_view(), name='chat_detail'), # GET/DELETE 
]
