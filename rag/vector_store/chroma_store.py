'''Store and search vectors using ChromaDB
   1. Stores vectors from your PDFs (1536 numbers each)
   2. Searches for similar vectors when farmers ask questions
   3. Returns relevant PDF chunks with metadata (filename, page)
'''

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
import numpy as np
#parent directory to path
sys.path.append(str(Path(__file__).parent.parent))
from logger.custom_logger import get_logger
from config.loader import config
from exception.custom_exception import BetaFarmException
# import chromadb
# from chromadb.config import Settings

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True

except ImportError:
    print('Warning: chromadb not installed. Run: pip install chromadb')

logger = get_logger(__name__).logger

class VectorDatabase:
    '''
    Stores and searches vectors using ChromaDB.
    '''
    
    # Class variable for singleton pattern
    _instance = None
    
    # Function to create single instance
    def __new__(cls):
        '''Creates only ONE instance of VectorDatabase.'''
        if cls._instance is None:
            logger.info('=' * 60)
            logger.info('CREATING VECTOR DATABASE (First and only instance)')
            logger.info('=' * 60)
            cls._instance = super().__new__(cls)
            
        return cls._instance
    
    # Function to initialize database
    def __init__(self):
        '''
        Initializes the vector database connection.
        Checks if already initialized (prevents double loading)
        Loads configuration from rag_config.yaml
        Creates ChromaDB client
        Initializes vector store
        '''
        
        # Check if already initialized (prevents double loading)
        if hasattr(self, '_initialized'):
            logger.warning('VectorDatabase already initialized, skipping...')
            return
        
        # Mark as initialized
        self._initialized = True
        
        logger.info('Initializing VectorDatabase...')
        
        
        # Get the 'vector_db' section from config
        vector_db_config = config.get('vector_db', {})
        
        # Get the 'embeddings' section from config
        embeddings_config = config.get('embeddings', {})
        
        # Database settings
        
        # Get database type ('chromadb' or 'faiss')
        self.database_type = vector_db_config.get('database_type', 'chromadb')
        
        # Where to save database files
        self.database_folder = vector_db_config.get('database_folder', './chroma_db')
        
        # Prefix for table names
        self.table_prefix = vector_db_config.get('table_prefix', 'farm_data')
        
        # Embedding settings
        active_provider = embeddings_config.get('active_provider', 'openai')
        openai_config = embeddings_config.get('openai', {})
        self.dimension = openai_config.get('dimension', 1536)
        
        # Build table name
        self.table_name = f"{self.table_prefix}_{active_provider}"
        
        # Log all settings
        logger.info(f'  Database Type: {self.table_name}')
        logger.info(f'  Database Folder: {self.database_folder}')
        logger.info(f'  Database Table: {self.database_type}')
        logger.info(f'  Vector Dimension: {self.dimension}')
        
        # Initialize chromadb
        if not CHROMADB_AVAILABLE:
            logger.error('ChromaDB not installed.')
            self.db = None
            self.table = None
            return
        
        try:
            # Connect to database
            self.db = chromadb.PersistentClient(
                path=self.database_folder,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Create or get table
            existing_tables = [col.name for col in self.db.list_collections()]
            
            if self.table_name in existing_tables:
                self.table = self.db.get_collection(self.table_name)
                
                logger.info(f'  Using existing table ({self.table.count()} vectors)')
            
            else:
                self.table = self.db.create_collection(
                    name=self.table_name,
                    metadata={"hnsw:space": "cosine", "dimension": self.dimension}
                )
                
                logger.info(f'  Created new table')
                
        except Exception as e:
            logger.error(f'Failed: {e}')
            self.db= None
            self.table = None
                
    
    # Save PDF chunks to database
    def store_vectors(self, vectors: np.ndarray, metadatas: List[Dict], ids:List[str]):
        '''
        Store PDF vectors in database.
        
        ARGS:
            vectors: Array of shape (num_chunks, 1536)
            metadatas: List of dicts with filename, page, text
            ids: Unique IDs for each vector
        '''
        
        if self.table is None:
            raise BetaFarmException('Database not ready')
        
        # Validate 
        if len(vectors) != len(metadatas) != len(ids):
            raise BetaFarmException('Length mismatch')
        
        if vectors.shape[1] !=self.dimension:
            raise BetaFarmException(f'Dimension mismatch: {vectors.shape[1]} vs {self.dimension}')
        
        # Extract documents (text) from metadatas
        documents = [
            m.get('text', m.get('page_content', '')) for m in metadatas
        ] 
        
        # Store with documents parameter
        self.table.add(
            embeddings=vectors.tolist(),
            metadatas=metadatas,
            ids=ids,
            documents=documents
        )
        
        logger.info(f'  Stored {len(vectors)} vectors')
        
    
    # search (Find similar vectors for farmer's question)
    def search(self, query_vector: np.ndarray, top_k: int = 5) -> List[Dict]:
        '''
        Search for similar vectors to farmer's question.
        
        ARGS:
            query_vector: Vector from encode_query() - shape (1536,)
            top_k: Number of results (default 5)
        
        RETURNS:
            List of dicts with text, filename, page, score
        '''
        
        if self.table is None:
            raise BetaFarmException('Database not ready')
        
        if len(query_vector) != self.dimension:
            raise BetaFarmException(f'Query dimension mismatch')
        
        # Search
        results = self.table.query(
            query_embeddings=[query_vector.tolist()],
            n_results=top_k,
            include=['metadatas', 'documents', 'distances']
        )

        # Format results
        formatted = []
        if results['ids'] and results['ids'][0]:
            
            for i in range(len(results['ids'][0])):
                formatted.append({
                    'text': results['documents'][0][i],
                    'filename': results['metadatas'][0][i].get('filename', 'Unknown'),
                    'page': results['metadatas'][0][i].get('page', 'N/A'),
                    'score': round(1 - results['distances'][0][i], 4)
                })
                
        return formatted
    
    
    # Count number of vectors
    def count(self) -> int:
        '''Return number of vectors in database.'''
        return self.table.count() if self.table else 0
    
# Create the singleton instance
vector_db = VectorDatabase()
            
if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Testing  Vector Database")
    print("=" * 60)
    
    if not CHROMADB_AVAILABLE:
        print("\n❌ ChromaDB not installed!")
        print("   Run: pip install chromadb")
        print("=" * 60)
        exit(1)
    
    print("\n1. Creating VectorDatabase instance...")
    db = VectorDatabase()
    
    print(f'\n  Table: {db.table_name}')
    print(f'    Vectors stored: {db.count()}')
    print(f"    Status: {'  Ready' if db.table else 'Failed'}")
    
