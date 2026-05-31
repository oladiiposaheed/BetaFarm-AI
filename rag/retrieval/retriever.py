import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.append(str(Path(__file__).parent.parent))

from logger.custom_logger import get_logger
from embeddings.embedding_generator import embedding_generator
from vector_store.chroma_store import vector_db

logger = get_logger(__name__).logger

class Retriever:
    '''
    Search for relevant PDF chunks when farmers ask questions
        #  Each result contains:
        # - text: The actual chunk
        # - filename: Which PDF it came from
        # - page: Page number
        # - score: Similarity score (0-1)
    '''
    
    _instance = None
    
    def __new__(cls):
        '''Singleton - only one instance.'''
        
        if cls._instance is None:
            logger.info('=' * 50)
            logger.info('CREATING RETRIEVER')
            logger.info('=' * 50)
            
            cls._instance = super().__new__(cls)
            
        return cls._instance
    
    
    def __init__(self):
        '''Initialize retriever and run once'''
        
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        logger.info('Initializing Retriever...')
        
        # Check if vector database is ready
        if vector_db.table is None:
            logger.warning('Vector database empty. Run ingest_all.py first.')
            self.ready = False
        
        else:
            self.ready = True
            logger.info(f'  Ready - {vector_db.count()} vectors available')
            
        logger.info('=' * 50)
        logger.info('RETRIEVER READY')
        logger.info('=' * 50)
        
        
    # Search method
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        '''
        Search for relevant PDF chunks.
        '''
        
        if not self.ready:
            logger.error('Retriever not ready')
            return []
        
        logger.info(f'Search: {query[:100]}')
        
        # Convert to vector 
        try:
            query_vector = embedding_generator.encode_query(query)
        
        except Exception as e:
            logger.error(f'Failed to encode: {e}')
            return []
        
        # Search database
        try:
            return vector_db.search(query_vector, top_k=top_k)
        
        except Exception as e:
            return []
        
    
    def get_table_count(self) -> int:
        '''Return number of chunks in database.'''
        
        return vector_db.count() if self.ready else 0
    
    
    def get_table_name(self) -> str:
        '''Return database table name'''
        
        return vector_db.table_name if self.ready else 'Not ready'
    
    
    def health_check(self) -> Dict[str, Any]:
        '''Check if retriever is ready'''
        
        return {
            'ready': self.ready,
            'vector_count': self.get_table_name()
        }
        
# Singleton instance
retriever = Retriever()


if __name__=='__main__':
    print('=' * 60)
    print('TESTING TASK RETRIEVER')
    print('=' * 60)
    
    ret = Retriever()
    
    # Health check
    print(f'\nReady: {ret.ready} | Vectors: {ret.get_table_count()} | Table: {ret.get_table_name()}')
    if not ret.ready:
        print('\n Run ingest_all.py first')
        exit(1)
        
    # Test queries
    queries = [
        'How to treat cassava mosaic disease?',
        'Rice production in northern Nigeria',
        'Maize disease prevention'
    ]
     
    for q in queries:
        print(f'\n {q[:100]}...')
        results = ret.search(q, top_k=2)
        
        if results:
            for r in results:
                print(f"    {r['filename']} (score: {r['score']:.3f})")
        
        else:
            print('     No results')
            

         