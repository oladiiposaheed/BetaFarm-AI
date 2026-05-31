# import sys
# from pathlib import Path
# from typing import List, Dict, Any

# sys.path.append(str(Path(__file__).parent.parent))
# from logger.custom_logger import get_logger

# logger = get_logger(__name__).logger

# try:
#     from sentence_transformers import CrossEncoder
#     CCROSS_ENCODER_AVAILABLE = True
    
# except ImportError:
#     CCROSS_ENCODER_AVAILABLE = False
#     print('Run: pip install sentence-transformers')
    

# class Reranker:
#     '''
#     Re-ranks search results using cross-encoder model.
#         1. Takes query and list of candidate documents
#         2. Cross-encoder scores each (query, document) pair
#         3. Sorts documents by new score (higher = more relevant)
#         4. Returns re-ranked results
#     '''
    
#     _instance = None
    
#     def __new__(cls):
#         '''Singleton - only one instance'''
        
#         if cls._instance is None:
#             logger.info('=' * 40)
#             logger.info('CREATING RERANKER')
#             logger.info('=' * 40)
#             cls._instance = super().__new__(cls)
#         return cls._instance
    
#     def __init__(self):
#         '''Initialize reranker with cross-encoder model.'''
        
#         if hasattr(self, '_initialized'):
#             return
        
#         self._initialized = True
#         logger.info('Initializing Reranker...')
        
#         # Load cross-encoder model
#         if CCROSS_ENCODER_AVAILABLE:
#             self.model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
#             self.is_ready = True
#             logger.info('Cross-encoder loaded')
            
#         else:
#             self.model = None
#             self.is_ready = False
#             logger.warning('sentence-transformers not installed')
            
#         logger.info('=' * 40)
#         logger.info('RERANKER READY')
#         logger.info('=' * 40)
        
#     def rerank(self, query: str, documents: List[Dict[str, Any]], top_k: int=5) -> List[Dict[str, Any]]:
#         '''
#         Re-rank documents by relevance to query.
#         RETURNS:
#             Re-ranked documents with 'rerank_score' added
#         '''
        
#         # If reranker not ready, return original documents
#         if not self.is_ready or not documents:
#             return documents[:top_k]
        
#         # Prepare (query, document) pairs
#         pairs = [
#             (query, doc.get('text', '')) for doc in documents
#         ]
        
#         # Get reranking scores
#         scores = self.model.predict(pairs)
        
#         # Add scores to documents
#         for i, doc in enumerate(documents):
#             doc['rerank_score'] = float(scores[i])
            
#         # Sort by rerank score (highest first)
#         documents.sort(key=lambda x: x.get('rerank_score', 0), reverse=True)
        
#         # Return top_k
#         return documents[:top_k]
    
            
# reranker = Reranker()

# if __name__=='__main__':
#     print('\n' + '=' * 40)
#     print('TESTING RERANKER')
#     print('=' * 40)
    
#     reranker = Reranker()
#     print(f'Ready: {reranker.is_ready}')
    
#     if reranker.is_ready:
#         # Test with sample data
#         test_query = 'cassava disease'
        
#         test_docs = [
#             {'text': 'How to grow tomatoes', 'filename': 'tomato.pdf'},
#             {'text': 'Cassava mosaic virus treatment', 'filename': 'cassava.pdf'},
#             {'text': 'Rice planting season', 'filename': 'rice.pdf'},
#         ]
        
#         results = reranker.rerank(test_query, test_docs, top_k=3)
#         print('\nReranked results:')
        
#         for r in results:
#             print(f"   Score: {r.get('rerank_score', 0):.4f} | {r['filename']}")
            
#     print('\n' + '=' * 60)
#     print('RERANKER READY')
#     print('=' * 60)