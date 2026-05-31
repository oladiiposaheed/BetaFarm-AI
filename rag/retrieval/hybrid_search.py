import sys
from pathlib import Path
from typing import List, Dict, Any

sys.path.append(str(Path(__file__).parent.parent))
from logger.custom_logger import get_logger
from retrieval.retriever import retriever
from retrieval.bm25_search import bm25_search
from retrieval.query_rewriter import query_rewriter

logger = get_logger(__name__).logger

class HybridSearch:
    '''
    Combines vector search and BM25 keyword search for optimal results
    '''
    
    # No instance exists yet
    _instance = None
    
    def __new__(cls):
        '''Create only ONE instance of HybridSearch.'''
        
        #No instance exists, so create one
        if cls._instance is None:
            logger.info('=' * 50)
            logger.info('CREATING HYBRID SEARCH (First instance)')
            logger.info('=' * 50)
            # Create the actual instance
            cls._instance = super().__new__(cls)
        return cls._instance
    
    # Initialize hybrid search
    def __init__(self):
        '''
        Initialize hybrid search and check if components are ready.
            - Checks if retriever (vector search) is ready
            - Checks if BM25 search is ready
            - Sets is_ready flag if both are ready
            - Sets default weights for combining scores
        '''
        
        # Skip if already initialized (singleton pattern)
        if hasattr(self, '_initialized'):
            logger.debug('HybridSearch already initialized, skipping...')
            return

        #Mark as initialized
        self._initialized = True
        logger.info('Initializing Hybrid Search...')
        
        # Check if vector retriever is ready, 'ready': if vector database is available
        vector_ready = getattr(retriever, 'ready', False)
        
        # Check if BM25 search is ready
        bm25_ready = getattr(bm25_search, 'ready', False)
        
        # Set is_ready flag
        self.is_ready = vector_ready and bm25_ready
        
        # Set weights for combining scores
        self.vector_weight = 0.7
        self.bm25_weight = 0.3
        
        if self.is_ready:
            logger.info(f'Hybrid Search ready')
            logger.info(f'Vector weight: {self.vector_weight}')
            logger.info(f'BM25 weight: {self.bm25_weight}')
            
        else:
            logger.warning('Hybrid Search not ready - missing components')
            
        
        logger.info('=' * 50)
        logger.info('HYBRID SEARCH INITIALIZED')
        logger.info('=' * 50)
        
        
    # Convert scores to 0-1 range
    def _normalize_scores(self, scores: List[float]) -> List[float]:
        '''
        Normalize a list of scores to range 0-1.
        
        ARGS:
            scores: List of raw scores (e.g., BM25 scores can be >1)
        
        RETURNS:
            List of normalized scores between 0 and 1
        '''
        
        # If no scores, return empty list
        if not scores:
            return []
        
        # Find maximum score in the list
        max_score = max(scores)
        
        # If max is 0, all scores are 0 (avoid division by zero)
        if max_score == 0:
            return [0.0] * len(scores)
        
        # Normalize each score by dividing by max
        return [score / max_score for score in scores]
    
    # Combine vector and BM25 results
    def _merge_results(self, vector_results: List[Dict], bm25_results: List[Dict]) -> List[Dict]:
        '''
        Merge vector and BM25 results into a single ranked list.
        ARGS:
            vector_results: List from retriever.search() (has 'score' key)
            bm25_results: List from bm25_search.search() (has 'bm25_score' key)
        
        RETURNS:
            Merged list with combined scores, sorted by hybrid_score
        '''
        
        combined = {}
        
        # Add vector results with their scores
        for item in vector_results:
            text = item.get('text', '')
            if text:
                combined[text] = {
                    'text': text,
                    'filename': item.get('filename', 'Unknown'),
                    'page': item.get('page', 'N/A'),
                    'vector_score': item.get('score', 0.0),
                    'bm25_score': 0.0,
                    'hybrid_score': item.get('score', 0.0) * self.vector_weight
                }
                
        # Add BM25 results and combine scores
        for item in bm25_results:
            # Extract the text content
            text = item.get('text', '')
            
            # Only process if text is not empty
            if text:
                # Get normalized BM25 score
                bm25_score = item.get('bm25_score', 0.0)
                
                # Check if this text already exists from vector search
                if text in combined:
                    # Case 1: Chunk exists from vector search
                    
                    # Update BM25 score
                    combined[text]['bm25_score'] = bm25_score
                    
                    # Recalculate hybrid score using both weights
                    combined[text]['hybrid_score'] = (
                        combined[text]['vector_score'] * self.vector_weight + bm25_score * self.bm25_weight
                    )
                    
                else:
                    # Case 2: Chunk only found by BM25 (not by vector)
                    # Create new entry with only BM25 score
                    combined[text] = {
                        'text': text,
                        'filename': item.get('filename', 'Unknown'),
                        'page': item.get('page', 'N/A'),
                        'vector_score': 0.0, # No vector score
                        'bm25_score': bm25_score,
                        'hybrid_score': bm25_score * self.bm25_weight # initial hybrid(only BM25)
                
                    }
        #Convert dictionary to list and sort by hybrid_score
        results = list(combined.values())
        results.sort(key=lambda x: x['hybrid_score'], reverse=True)
        
        return results
        
        
    # Hybrid search method
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        '''
        Perform hybrid search combining vector and BM25.
            1. Check if hybrid search is ready
            2. Get vector results (semantic)
            3. Get BM25 results (keyword)
            4. Normalize BM25 scores to 0-1
            5. Merge and combine scores
            6. Return top_k results
        '''
        
        # Validate that hybrid search is ready
        
        # Check if both vector and BM25 components are available
        if not self.is_ready:
            logger.error('Hybrid search not ready - missing components')
            return []
        
        # Check if query is valid (not empty and is a string)
        if not query or not isinstance(query, str):
            return []
        
        logger.info(f'Hybrid search: "{query[:50]}"')
        
        # Use improved query rewriting for better results 
        #improved_query = query_rewriter.rewrite(query)
        
        
        improved_query = query
        #Get vector search results (semantic meaning)
        vector_results = retriever.search(query, top_k=top_k * 2)
        
        vector_results = retriever.search(improved_query, top_k=top_k * 2)
        
        logger.debug(f'   Vector results: {len(vector_results)}')
        
        # Get BM25 search results (keyword matching)
        bm25_raw_results = bm25_search.search(improved_query, top_k=top_k * 2)
        logger.debug(f'    BM25 raw results: {len(bm25_raw_results)}')
        
        # Normalize BM25 scores to 0-1 range
        
        # Extract all BM25 scores into a list
        bm25_scores = [r.get('bm25_score', 0.0) for r in bm25_raw_results]
        normalized_bm25_scores = self._normalize_scores(bm25_scores)
        
        # Apply normalized scores back to BM25 results
        # Create a new list with updated scores
        bm25_results = []
        for i, item in enumerate(bm25_raw_results):
            # Update the bm25_score with normalized value
            item['bm25_score'] = normalized_bm25_scores[i]
            bm25_results.append(item)
            
        # Merge and combine scores from both searches
        merged_results = self._merge_results(vector_results, bm25_results)
        
        # Return top_k results
        final_results = merged_results[:top_k]
        logger.info(f'   Hybrid results: {len(final_results)}')
        
        # Return final ranked results
        return final_results
    
# Create the singleton instance
hybrid_search = HybridSearch()

if __name__=='__main__':
    print('\n' + '=' * 60)
    print('HYBRID SEARCH')
    print('=' * 60)
    
    # Create hybrid search instance
    hybrid = HybridSearch()
    
    # Print initialization status
    print(f"\n✅ Hybrid Search Ready: {hybrid.is_ready}")
    print(f"   Vector weight: {hybrid.vector_weight}")
    print(f"   BM25 weight: {hybrid.bm25_weight}")

    # List of test queries to verify hybrid search works
    test_queries = [
        'How to treat cassava mosaic disease?',
        'TME 419 cassava variety',
        'rice production in northern Nigeria'
    ]
        
    # Loop through each test query
    for query in test_queries:
        print(f'\n Query: {query}')
        
        # Perform hybrid search
        results = hybrid.search(query, top_k=3)
        
        # Display results if found
        if results:
            for i, r in enumerate(results, 1):
                print(f'\n   Result {i}:')
                print(f"      File: {r['filename']}")
                print(f"      Page: {r['page']}")
                print(f"      Hybrid Score: {r['hybrid_score']:.4f}")
                print(f"      Vector Score: {r['vector_score']:.4f}")
                print(f"      BM25 Score: {r['bm25_score']:.4f}")
                print(f"      Text: {r['text'][:100]}...")
                
        else:
            print('    No results found')
            
