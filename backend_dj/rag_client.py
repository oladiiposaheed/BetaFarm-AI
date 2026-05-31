'''
Handle communication between Django and RAG FastAPI service
    - Sends farmer questions to RAG service (port 8002)
    - Handles retries if RAG service is temporarily unavailable
    - Manages timeouts to prevent hanging requests
    - Returns formatted answers and sources to Django views
'''

import time
import requests
import logging
from django.conf import settings


logger = logging.getLogger(__name__)

class RAGClient:
    '''
    Client for communicating with RAG (Retrieval-Augmented Generation) service.
        - Takes farmer's question
        - Searches PDF knowledge base
        - Returns answer with sources
    '''
    
    def __init__(self):
        '''
        Initialize RAG client with configuration from settings.
            - Reads RAG service URL from Django settings
            - Sets timeout value
            - Sets maximum retry attempts
            - Creates HTTP session for connection reuse
        '''
        
        # Get RAG service URL from settings
        self.service_url = getattr(settings, 'RAG_SERVICE_URL', 'http://localhost:8002')
        
        # Get timeout value
        self.timeout = getattr(settings, 'RAG_TIMEOUT', 30)
        
        # Get maximum retry attempts
        self.max_retries = getattr(settings, 'RAG_MAX_RETRIES', 3)
        
        # Session reuses TCP connections for better performance
        self.http_session = requests.Session()
        
        # Set default headers for all requests
        self.http_session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        logger.info(f'RAG Clent initialized -URL: {self.service_url}, Timeout: {self.timeout}s')
        
        
    def ask(self, question: str, top_k: int = 5):
        '''
        Send question to RAG service and get answer.
        '''
        
        #1 Validate input
        if not question or not isinstance(question, str):
            logger.error(f'Invalid question: {question}')
            
            return {
                'answer': '',
                'sources': [],
                'success': False,
                'error': 'Invalid question provided'
            }
            
        #2 Build request data
        rag_data = {
            'question': question.strip(),
            'top_k': top_k
        }
        
        #3 Build complete URL for RAG endpoint
        rag_endpoint = f'{self.service_url}/api/v1/chat'
        
        #4 Track retry attempts
        last_error = None
        
        #5 Try to send request with retries
        for attempt in range(self.max_retries):
            try:
                logger.debug(f'Attempt {attempt + 1}/{self.max_retries} - Sending to RAG')
                
                #5 Send POST request to RAG service
                rag_response = self.http_session.post(
                    rag_endpoint,
                    json=rag_data,
                    timeout=self.timeout
                )
                
                #6 Check if request was successful
                if rag_response.status_code == 200:
                    # Success! Parse JSON response
                    response_data = rag_response.json()
                    
                    logger.info(f"RAG answered: {len(response_data.get('answer'))} chars")
                    
                    # Return success response
                    return {
                        'answer': response_data.get('answer', ''),
                        'sources': response_data.get('sources', []),
                        'success': True,
                        'error': None
                    }
                    
                else:
                    # Non-200 status code (e.g., 500, 404)
                    last_error = f'RAG service returned {rag_response.status_code}'
                    logger.warning(f'Attempt {attempt + 1} failed: {last_error}')
            
            except requests.exceptions.Timeout:
                # Request took too long (over timeout seconds)
                last_error = f'Request timeout after {self.timeout}s'
                logger.warning(f'Attempt {attempt + 1} timeout')
                
            except requests.exceptions.ConnectionError:
                # Cannot connect to RAG service (not running or wrong URL)
                last_error = 'Cannot connect to RAG service'
                logger.warning(f'Attempt {attempt + 1} connection error')
            
            except Exception as e:
                # Any other unexpected error
                last_error = str(e)
                logger.warning(f'Attempt {attempt + 1} error: {e}')
                
            # Wait before retry
            # Wait longer each time: 1s, 2s, 4s...
            if attempt < self.max_retries - 1:
                wait_time = 2 * attempt
                logger.debug(f'Waiting {wait_time}s before retry...')
                time.sleep(wait_time)
                
        # All retries failed - return error
        logger.error(f'All {self.max_retries} attempts failed. Last error: {last_error}')
        
        return {
            'answer': '',
            'success': [],
            'success': False,
            'error': last_error or 'Unknown error occurred'
        }
        
        
    def health_check(self) -> bool:
        '''
        Check if RAG service is healthy and responding.
        '''
        
        try:
            # Send health check request to RAG service
            health_url = f'{self.service_url}/api/v1/health'
            rag_response = self.http_session.get(
                health_url,
                timeout=5
            )
        
            # Service is healthy if status is 200 OK
            is_healthy = rag_response.status_code == 200
            logger.debug(f"Health check: {'OK' if is_healthy else 'Failed'}")
            
            return is_healthy
    
        except Exception as e:
            logger.warning(f'Health check failed: {e}')
            return False
        
# Create single instance that all views will share
rag_client = RAGClient()


if __name__=='__main__':
    print('\n' + '=' * 60)
    print('TESTING RAG CLIENT')
    print('=' * 60)
    
    # Health check
    print('\n Health Check:')
    
    rag = RAGClient()
    is_healthy = rag.health_check()
    print(f'    RAG Service healthy: {is_healthy}')
    
    if not is_healthy:
        print('\n    RAG service not running!')
        exit(1)
        
    # Ask a question
    print('\n ASK QUESTION:')
    test_question = 'What are the common diseases affecting tomato and how to treat tomato disease?'
    print(f'    Question: {test_question}')
    
    result = rag.ask(test_question, top_k=3)
    
    if result['success']:
        print(f"\n    Answer: {result['answer']}")
        print(f"\n    Sources: {len(result['sources'])} found")
        
        for src in result['sources'][:2]:
            print(f"      - {src.get('filename', 'Unknown')} (relevance: {src.get('relevance', 0):.2f})")
            
    else:
        print(f"\n    Error: {result['error']}")
        
    print('\n' + '=' * 60)
    print('RAG CLIENT TEST COMPLETE')
    print('=' * 60)    
