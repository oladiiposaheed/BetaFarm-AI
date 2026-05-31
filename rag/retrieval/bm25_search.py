import sys
import pickle
from pathlib import Path
from typing import List, Dict, Any
import re
from rank_bm25 import BM25Okapi
import string

sys.path.append(str(Path(__file__).parent.parent))
from logger.custom_logger import get_logger
from exception.custom_exception import BetaFarmException
from vector_store.chroma_store import vector_db

try:
    BM25_AVAILABLE = True

except Exception as e:
    BM25_AVAILABLE = False
    print('rank_bm25 not installed')
    
# Create logger for this file
logger = get_logger(__name__).logger


class BM25Search:
    '''search using BM25 algorithm.'''
    
    #Store the single instance
    _instance = None
    
    # Creates single instance
    def __new__(cls):
        '''
        Creates only ONE instance of BM25Search
        - Only ONE object of this class can ever exist
        - All parts of your code share the SAME BM25 index
        - Saves memory (not loading 2353 chunks multiple times)
        '''
        
        #Check if an instance already exists
        if cls._instance is None:
            # No instance exists, so create one
            logger.info('=' * 60)
            logger.info('CREATING BM25 SEARCH (First instance)')
            logger.info('=' * 60)
            
            #Create the actual instance
            cls._instance = super().__new__(cls)
            
        # Return the instance (either newly created or existing)
        return cls._instance
    
    
    # Initialize BM25 Search
    def __init__(self):
        '''
        Initialize BM25 search and load or build the keyword index.
        '''
        #Check if already initialized
        if hasattr(self, '_initialized'):
            # Already loaded, skip initialization
            logger.debug('BM25Search already initialized, skipping...')
            return 
        
        # Mark as initialized
        self._initialized = True
        logger.info('Initializing BM25 Search...')
        
        # Check if BM25 library is installed
        if not BM25_AVAILABLE:
            logger.info('rank_bm25 not installed. Run: pip install rank-bm25')
            self.ready = False # can't search
            return # Exit early
        
        # Path to save/load BM25 index
        self.index_path = Path(__file__).parent / 'bm25_index.pkl' 
        
        # Check the load existing index
        if self.index_path.exists():
            logger.info(f'  Loading existing BM25 index from: {self.index_path}')
            
            try:
                # Open the file in binary read mode
                with open(self.index_path, 'rb') as f:
                    # reads the saved
                    saved = pickle.load(f)
                    
                    # Restore the BM25 index object, lists of chunks, metadata
                    self.bm25 = saved['bm25']
                    self.chunks = saved['chunks']
                    self.metadatas = saved['metadatas']
                    
                logger.info(f'  Loaded BM25 index with {len(self.chunks)} chunks')
                    
                # Mark as ready - BM25 can now search
                self.ready = True
                return
            
            except Exception as e:
                logger.warning(f'  Failed to load index: {e}. rebuilding...')
            
        # Build new BM25 index from database(if no index file exists or loading the existing index failed)
        
        logger.info('   Building BM25 index from vector database...')
        
        self._build_index_from_database()
        
        
    # Build BM25 from vector DB
    def _build_index_from_database(self):
        '''
        Build BM25 index by loading all chunks from vector database.
            1. Connects to ChromaDB vector database
            2. Retrieves ALL stored text chunks (2353 of them)
            3. Tokenizes each chunk (splits into clean words)
            4. Builds BM25 index using tokenized chunks
            5. Saves index to disk for faster future loads
        '''
        
        # Check if database has vectors
        if vector_db.count() == 0:
            logger.warning('    Database is empty. Run ingest_all.py first.')
            self.ready = False
            return
        
        logger.info(f'  Loading {vector_db.count()} chunks from database...')
        
        # Check all chunks from vectordb
        results = vector_db.table.get(include=['documents', 'metadatas'])
        
        # Extract chunks and metadata
        raw_chunks = results['documents']
        raw_metadatas = results['metadatas']
        
        logger.info(f'  Raw chunks loaded: {len(raw_chunks)}')
        
        # Show first chunk sample
        if len(raw_chunks) > 0 and raw_chunks[0] is not None:
            print(f'    SAMPLE: First chunk = {raw_chunks[0][:100]}')
        else:
            print(f'    SAMPLE: First chunk is None or empty')
        
        # Clean and tokenize chunks
        logger.info(' Tokenizing chunks...')
        
        tokenized_chunks = []
        self.chunks = []
        self.metadatas = []
        
        for i, chunk in enumerate(raw_chunks):
            # Skip None chunks
            if chunk is None:
                continue
            
            # Skip non-string chunks
            if not isinstance(chunk, str):
                continue
            
            # Skip empty chunks
            if len(chunk.strip()) == 0:
                continue
            
            # clean text
            text = chunk.lower()
            
            # Remove punctuation (keep letters and spaces only)
            #text = re.sub(r'[^a-z\s]', '', text)
        
            # Split text t wordss
            words = text.split()
            
            # # remove very short words (1 character)
            # words = [
            #     w for w in words if len(w) > 1
            # ]
            
            # Only add words
            if words:
                tokenized_chunks.append(words)
                self.chunks.append(chunk)
                self.metadatas.append(raw_metadatas[i])
        
        print(f'tokenized_chunks length: {len(tokenized_chunks)}')
        print(f'Chunk length: {len(self.chunks)}')
        
        # Show first tokenized sample
        if len(tokenized_chunks) > 0:
            print(f'    SAMPLE tokens: {tokenized_chunks[0][:10]}')
            
        if len(tokenized_chunks) == 0:
            logger.error('  No valid chunks found!')
            self.ready = False
            return
        
        # Build BM25 Index
        logger.info('   Building BM25 index...')
        self.bm25 = BM25Okapi(tokenized_chunks)
        
        # Save index to disk
        logger.info(f'  Saving BM25 index to {self.index_path}')
        
        with open(self.index_path, 'wb') as f:
            pickle.dump({
                'bm25': self.bm25,
                'chunks': self.chunks,
                'metadatas': self.metadatas
            }, f)
            
        logger.info(f'  BM25 index built {len(self.chunks)} chunks indexed')
        self.ready = True
        
        
    def search(self, query: str, top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for chunks using BM25 keyword matching.
        
        ARGS:
            query: Farmer's question (e.g., "TME 419 cassava variety")
            top_k: Number of results to return (default 10)
        
        RETURNS:
            List of dicts with: text, filename, page, bm25_score
        """
        
        # Check if BM25 is ready
        if not self.ready:
            logger.error('BM25 not ready')
            return []
        
        if not query:
            return []
        
        logger.info(f'  BM25 search: "{query[:50]}"')
        
        # Tokenize query
        tokenized_query = self._tokenize_text(query)
        
        # Get BM25 scores
        scores = self.bm25.get_scores(tokenized_query)
        
        # Get top_k indices
        top_indices = scores.argsort()[::-1][:top_k]
        
        # Build results
        results = []
        for idx in top_indices:
            if scores[idx] <= 0:
                continue
            
            results.append({
                'text': self.chunks[idx],
                'filename': self.metadatas[idx].get('filename', 'Unknown'),
                'page': self.metadatas[idx].get('page', 'N/A'),
                'bm25_score': float(scores[idx])
            })
        
        logger.info(f'    Found {len(results)} BM25 matches')
        return results
    
    
    # Tokenize text
    def _tokenize_text(self, text: str) -> List[str]:
        '''
        Convert text into list of clean words (tokens).
            1. Converts to lowercase
            2. Removes punctuation
            3. Splits into words
            4. Removes common stopwords
            5. Removes very short words (1 character)
            
        ARGS:
            text: Raw text chunk or query
        
        RETURNS:
            List of clean words
        '''
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(f'[^\w\s]', ' ', text)
        
        # Remove numbers
        text = re.sub(r'\d+', ' ', text)
        
        # Split into words
        words = text.split()
        
        # Remove common stopwords
        stopwords = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'this', 'these', 'those',
            'they', 'we', 'you', 'she', 'he', 'it', 'them', 'their'
        }
        
        # Keep only words
        words = [w for w in words if w not in stopwords and len(w) > 1]

        return words        
        

        
bm25_search = BM25Search()
    
    
if __name__=='__main__':
    # print('\n' + '=' * 60)
    # print('TESTING FUNCTION 1: __new__ (Singleton)')
    # print('=' * 60)
    
    # # Create first instance
    # print('\n1.  Creating first BM25Search instance...')
    # bm1 = BM25Search()
    # print(f'    Instance 1 ID: {id(bm1)}')
    
    # # Create second instance
    # print('\n1.  Creating second BM25Search instance...')
    # bm2 = BM25Search()
    # print(f'    Instance 1 ID: {id(bm2)}')
    
    # # Check if they are the same object
    # print('\n3. Checking if both instances are the SAME object:')
    # print(f'    bm1 is bm2: {bm1 is bm2}')
    
    # if bm1 is bm2:
    #     print('\n   SINGLETON WORKING! Both variables point to same object')
    # else:
    #     print('\n   SINGLETON FAILED! Different objects were created')

    print('TESTING FUNCTION 2: __init__')
    print('=' * 50)
    print('TESTING FUNCTION 2: __init__')
    print('=' * 50)

    #bm = BM25Search()
    
   # Create instance
    bm = BM25Search()
    
    # Show results
    print(f"\n Ready: {bm.ready if hasattr(bm, 'ready') else 'Building...'}")
    print(f" Index path: {bm.index_path}")
    
    if hasattr(bm, 'chunks'):
        print(f" Chunks loaded: {len(bm.chunks)}")
    else:
        print(" Chunks: Building index (first time)")
    
    print("=" * 50)
    
    
