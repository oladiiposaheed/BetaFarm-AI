"""
FILE: rag/llm/chat.py - FIXED VERSION
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

sys.path.append(str(Path(__file__).parent.parent))
from logger.custom_logger import get_logger 
from config.loader import config
from retrieval.hybrid_search import hybrid_search

try:
    from langchain_groq import ChatGroq
    from langchain_openai import ChatOpenAI
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

logger = get_logger(__name__).logger


class FarmerChat:
    """Generate answers for farmers with memory that respects crop changes."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            logger.info('=' * 40)
            logger.info('CREATING FARMER CHAT')
            logger.info('=' * 40)
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        logger.info('Initializing Farmer Chat System...')
        
        self.session_histories = {}
        self.last_crop = {}
        
        logger.info('Memory: Enabled')
        
        llm_config = config.get('llm', {})
        self.temperature = llm_config.get('temperature', 0.3)
        self.max_tokens = llm_config.get('max_tokens', 3000)
        
        self.llm = None
        self.is_ready = False
        
        if LANGCHAIN_AVAILABLE:
            groq_key = os.getenv('GROQ_API_KEY')
            if groq_key:
                try:
                    self.llm = ChatGroq(
                        api_key=groq_key,
                        model='llama-3.1-8b-instant',
                        temperature=self.temperature,
                        max_tokens=self.max_tokens
                    )
                    self.is_ready = True
                    logger.info('Using Groq')
                except Exception as e:
                    logger.warning(f'Groq failed: {e}')
            
            if not self.is_ready:
                openai_key = os.getenv('OPENAI_API_KEY')
                if openai_key:
                    try:
                        self.llm = ChatOpenAI(
                            api_key=openai_key,
                            model='gpt-4o-mini',
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                        self.is_ready = True
                        logger.info('Using OpenAI')
                    except Exception as e:
                        logger.warning(f'OpenAI failed: {e}')
        
        if hybrid_search.is_ready:
            logger.info('Search system ready')
        
        logger.info('FARMER CHAT READY')
    
    def _get_history(self, session_id: str) -> list:
        if session_id not in self.session_histories:
            self.session_histories[session_id] = []
        return self.session_histories[session_id]
    
    def _detect_crop(self, text: str) -> str:
        """Detect which crop is mentioned in the text."""
        crops = {
            'apple': ['apple', 'apples', 'apple tree'],
            'cassava': ['cassava', 'cassava plant'],
            'maize': ['maize', 'corn'],
            'rice': ['rice'],
            'potato': ['potato', 'potatoes'],
            'tomato': ['tomato', 'tomatoes'],
            'wheat': ['wheat'],
            'soybean': ['soybean', 'soya']
        }
        
        text_lower = text.lower()
        for crop, keywords in crops.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return crop
        return None
    
    def _get_current_crop(self, session_id: str, question: str) -> str:
        """Get current crop from question or history."""
        # First check if question mentions a crop
        crop_in_question = self._detect_crop(question)
        if crop_in_question:
            return crop_in_question
        
        # Otherwise use last crop from memory
        return self.last_crop.get(session_id, 'cassava')
    
    def _search(self, question: str, top_k: int = 5) -> tuple:
        """Search for relevant chunks."""
        search_results = hybrid_search.search(question, top_k=top_k)
        
        if not search_results:
            return '', []
        
        context_parts = []
        sources = []
        
        for i, r in enumerate(search_results, 1):
            text = r.get('text', '')
            filename = r.get('filename', 'Unknown')
            score = r.get('hybrid_score', 0)
            
            if text:
                context_parts.append(f'[{i}] From {filename}:\n{text}\n')
                sources.append({
                    'filename': filename,
                    'page': r.get('page', 'N/A'),
                    'relevance': score
                })
        
        context = '\n'.join(context_parts)
        return context, sources
    
    def ask(self, question: str, session_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """Answer farmer's question."""
        
        if session_id is None:
            session_id = str(uuid4())
        
        if not self.is_ready:
            # Use the search results directly as answer
            context, sources = self._search(question, top_k)
            if context:
                # Return first relevant chunk as answer
                answer = f"Based on your PDF documents:\n\n{context}"
                return {'answer': answer, 'sources': sources[:3]}
        else:
            return {
                'answer': "Please add your API keys (GROQ_API_KEY or OPENAI_API_KEY) to enable AI responses. For now, your PDFs are loaded but I can't generate answers.", 'sources': []
            }
        
        if not hybrid_search.is_ready:
            return {'answer': 'Search system not ready. Run ingest_all.py', 'sources': []}
        
        if not question:
            return {'answer': 'Please ask a question.', 'sources': []}
        
        logger.info(f'Q: {question[:100]}')
        
        # Detect crop from question
        current_crop = self._get_current_crop(session_id, question)
        logger.info(f'Current crop: {current_crop}')
        
        # Update last crop for this session
        self.last_crop[session_id] = current_crop
        
        # Build search query
        search_query = question
        if current_crop and current_crop not in question.lower():
            search_query = f"{current_crop} {question}"
        
        # Search
        context, sources = self._search(search_query, top_k)
        
        if not context:
            return {
                'answer': f'No information found about {current_crop}. Please add relevant PDFs.',
                'sources': []
            }
        
        # Get conversation history
        history = self._get_history(session_id)
        history_text = ""
        for h in history[-4:]:
            history_text += f"User: {h['question']}\nAssistant: {h['answer']}\n"
        
        # Build prompt
        prompt = f"""You are BetaFarm AI, an agricultural assistant.

CONVERSATION HISTORY:
{history_text}

CURRENT QUESTION: {question}
CROP: {current_crop}

RELEVANT INFORMATION:
{context}

Answer the question specifically about {current_crop}. Use the information provided.
If the question mentions a different crop, answer about that crop instead.

ANSWER:"""

        try:
            response = self.llm.invoke(prompt)
            answer = response.content.strip()
            
            # Clean up
            answer = re.sub(r'\*\*(.*?)\*\*', r'\1', answer)
            
            # Save to history
            history.append({'question': question, 'answer': answer})
            
            # Keep last 20
            if len(history) > 20:
                self.session_histories[session_id] = history[-20:]
            
            return {
                'answer': answer,
                'sources': sources[:3]
            }
            
        except Exception as e:
            logger.error(f'Generation failed: {e}')
            return {
                'answer': f'Sorry, I had trouble generating an answer.',
                'sources': sources[:3] if sources else []
            }
    
    def clear_memory(self, session_id: str):
        if session_id in self.session_histories:
            self.session_histories[session_id] = []
        if session_id in self.last_crop:
            self.last_crop[session_id] = 'cassava'
        logger.info(f'Memory cleared')


farmer_chat = FarmerChat()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("TESTING")
    print("=" * 50)
    
    chat = FarmerChat()
    test_session = 'test123'
    
    q1 = 'What are apple diseases?'
    print(f'\nQ: {q1}')
    r1 = chat.ask(q1, session_id=test_session, top_k=3)
    print(f"A: {r1['answer'][:200]}...")
    
    print('\n✅ Test complete')