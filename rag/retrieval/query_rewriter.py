import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from groq import Groq
from openai import OpenAI

sys.path.append(str(Path(__file__).parent.parent))
from logger.custom_logger import get_logger
from config.loader import config

logger = get_logger(__name__).logger


class QueryRewriter:
    '''
    Improves farmer questions for better search results using LLM.
    '''
    
    #only one instance
    _instance = None
    
    def __new__(cls):
        '''Create only ONE instance of QueryRewriter.'''

        if cls._instance is None:
            logger.info('=' * 40)
            logger.info('CREATING QUERY REWRITER')
            logger.info('=' * 40)
            
            cls._instance = super().__new__(cls)
            
        return cls._instance
    
    def __init__(self):
        '''Initialize query rewriter with Groq or OpenAI.'''
        
        # Skip if already initialized
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        logger.info('Initializing Query Rewriter...')
        
        # Get LLM configuration
        llm_config = config.get('llm', {})
        
        # Storage for LLM API connection
        self.llm_api = None
        self.llm_model = None
        self.is_ready = False
        
        # GROQ
        groq_api_key = os.getenv('GROQ_API_KEY')
        if groq_api_key:
            
            try:
                self.llm_api = Groq(api_key=groq_api_key)
                self.llm_model = llm_config.get('groq', {}).get('model', 'llama-3.1-8b-instant')
                
                self.is_ready = True
                logger.info(f' Using Groq: {self.llm_model}')
            
            except Exception as e:
                logger.warning(f'Groq failed: {e}')
                
        # FALLBACK TO OPENAI
        if not self.is_ready:
            openai_api_key = os.getenv('OPENAI_API_KEY')
            
            if openai_api_key:
                try:
                    self.llm_api = OpenAI(api_key=openai_api_key)
                    self.llm_model = llm_config.get('openai', {}).get('model', 'gpt-4o-mini')
                    
                    self.is_ready = True
                    logger.info(f'  USing OpenAI: {self.llm_model}')
                
                except Exception as e:
                    logger.warning(f'OpenAI failed: {e}')
        
        if not self.is_ready:
            logger.warning('    No LLM available. Query rewriting disabled')
            
            
    def rewrite(self, original_query: str) -> str:
        '''
        Rewrite farmer's question for better search results.
        '''
        
        # If LLM not ready, return original query unchanged
        if not self.is_ready:
            return original_query
        
        # Skip empty or invalid queries
        if not original_query or not isinstance(original_query, str):
            return original_query or ''
        
        logger.info(f'  Original: "{original_query[:50]}"')
        
        # Build prompt for LLM
        rewrite_prompt = f"""
            Convert this farmer's question into a better search query.
            
            Rules:
                - Keep important agricultural terms (cassava, maize, disease, treatment)
                - Add relevant keywords (symptoms, causes, prevention)
                - Remove filler words (my, the, a, an)
                - Use technical terms ("yellowing" instead of "turning yellow")
                - Keep under 15 words
                
            Farmer question: "{original_query}"
            
            Better search query:
        """
        
        try:
            llm_response = self.llm_api.chat.completions.create(
                model=self.llm_model,
                messages=[
                    {
                        'role': 'system',
                        'content': 'You are a search query optimizer for agriculture. Output only the rewritten query, no explanations.'
                    },
                    
                    {
                        'role': 'user',
                        'content': rewrite_prompt
                    }
                ],
                
                temperature=0.3, # Consistent results
                max_tokens=180 # Short response
            )
            
            # Extract rewritten query
            rewritten_query = llm_response.choices[0].message.content.strip()
            
            # Remove quotes if present
            rewritten_query = rewritten_query.strip('"').strip("'")
            
            # If rewriting failed, use original
            if not rewritten_query or len(rewritten_query) < 3:
                logger.warning('   Rewriting returned empty, using original')
                
                return original_query
            
            logger.info(f'  Rewritten: "{rewritten_query[:50]}"')
            return rewritten_query
        
        except Exception as e:
            logger.error(f' Rewriting failed: {e}')
            return original_query
        
    # For batch processing
    def rewrite_multiple(self, queries: List[str]) -> List[str]:
        '''
        Rewrite multiple queries at once.
        
        ARGS:
            queries: List of farmer questions
        
        RETURNS:
            List of rewritten queries
        '''
        
        return [self.rewrite(q) for q in queries]
    
    
# SINGLETON INSTANCE
query_rewriter = QueryRewriter()


if __name__=='__main__':
    print('\n' + '=' * 60)
    print('TESTING QUERY REWRITER')
    print('=' * 60)
    
    rewriter = QueryRewriter()
    print(f'\n Ready: {rewriter.is_ready}')
    
    if rewriter.is_ready:
        # Test queries
        test_queries = [
            'my cassava leaves are turning yellow',
            'how to stop maize from getting diseases',
            'rice not growing well in my farm',
            'treat cassava mosaic'
        ]
        
        print('\n   REWRITING RESULTS:')
        print('=' * 60)
        
        for original in test_queries:
            rewritten = rewriter.rewrite(original)
            print(f'   Original: {original}')
            print(f'   Rewritten: {rewritten}')
            
    else:
        print('\n   Nl LLM available.')
        print('    Add GROQ_API_KEY or OPENAI_API_KEY to .env file')
        