from django.db import models
from django.conf import settings

# Create your models here.

class ChatHistory(models.Model):
    '''
    Stores each farmer question and answer.
    
    Each record is one conversation turn:
        - Farmer asks question
        - RAG system answers
    '''
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats', verbose_name='Farmer')
    question = models.TextField(verbose_name='Question', help_text="Farmer;s question")
    answer = models.TextField(verbose_name='Answer', help_text='Generated answer from RAG system')
    sources = models.JSONField(default=list, verbose_name='Sources', help_text='List of PDF sources used for answer')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At', help_text='When the question was asked')
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Chat History'
        verbose_name_plural = 'Chat Histories'
        
    def __str__(self):
        return f'{self.user.phone_number} - {self.question[:50]}'
    
    