"""
FILE: rag/embeddings/embedding_generator.py
PURPOSE: Convert text into vectors using OpenAI

WHAT THIS FILE DOES:
    1. Takes text (like "cassava disease treatment")
    2. Converts it to a vector (list of 1536 numbers)
    3. Uses OpenAI embeddings (fast, reliable, works now)
    4. Groq will handle translation (Yoruba/Hausa/Igbo)
"""

import os
import sys
from pathlib import Path
from typing import List
import numpy as np

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from logger.custom_logger import get_logger
from config.loader import config
from exception.custom_exception import BetaFarmException
from openai import OpenAI

logger = get_logger(__name__).logger


# ============================================================
# EMBEDDING GENERATOR CLASS (OpenAI Only)
# ============================================================

class EmbeddingGenerator:
    """Converts text to vectors using OpenAI embeddings."""
    
    _instance = None
    
    # ============================================================
    # FUNCTION 1: __new__ (Singleton)
    # ============================================================
    def __new__(cls):
        """Creates only ONE instance."""
        
        if cls._instance is None:
            logger.info('=' * 60)
            logger.info('CREATING EMBEDDING GENERATOR (OpenAI)')
            logger.info('=' * 60)
            cls._instance = super().__new__(cls)
        
        return cls._instance
    
    # ============================================================
    # FUNCTION 2: __init__ (Initialize)
    # ============================================================
    def __init__(self):
        """Initializes OpenAI client."""
        
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        logger.info('Initializing EmbeddingGenerator...')
        
        # Load config
        self.config = config
        embeddings_config = self.config.get('embeddings', {}).get('openai', {})
        
        # Settings
        self.model = embeddings_config.get('model', 'text-embedding-3-small')
        self.dimension = embeddings_config.get('dimension', 1536)
        self.normalize = embeddings_config.get('normalize', True)
        self.batch_size = embeddings_config.get('batch_size', 32)
        
        # Get API key
        api_key_env = embeddings_config.get('api_key_env', 'OPENAI_API_KEY')
        api_key = os.getenv(api_key_env)
        
        if not api_key:
            logger.error(f'OpenAI API key not found in {api_key_env}')
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            logger.info(f'OpenAI ready - Model: {self.model}, Dim: {self.dimension}')
        
        logger.info('EmbeddingGenerator ready!')
    
    # ============================================================
    # FUNCTION 3: encode_query (Question to vector)
    # ============================================================
    def encode_query(self, text: str) -> np.ndarray:
        """Convert farmer question to vector."""
        
        if not self.client:
            raise BetaFarmException('OpenAI client not available')
        
        text = text.strip()[:1000]
        
        response = self.client.embeddings.create(
            model=self.model,
            input=text,
            encoding_format="float",
            timeout=120.0
        )
        
        vector = np.array(response.data[0].embedding, dtype=np.float32)
        
        if self.normalize:
            norm = np.linalg.norm(vector)
            if norm > 0:
                vector = vector / norm
        
        return vector
    
    # ============================================================
    # FUNCTION 4: encode_documents (PDF chunks to vectors)
    # ============================================================
    def encode_documents(self, texts: List[str]) -> np.ndarray:
        """Convert multiple PDF chunks to vectors."""
        
        if not self.client:
            raise BetaFarmException('OpenAI client not available')
        
        if not texts:
            return np.array([])
        
        cleaned_texts = [t for t in texts if t and t.strip()]
        if not cleaned_texts:
            return np.array([])
        
        all_vectors = []
        
        for i in range(0, len(cleaned_texts), self.batch_size):
            batch = cleaned_texts[i:i + self.batch_size]
            
            response = self.client.embeddings.create(
                model=self.model,
                input=batch,
                encoding_format="float"
            )
            
            for data in response.data:
                vector = np.array(data.embedding, dtype=np.float32)
                if self.normalize:
                    norm = np.linalg.norm(vector)
                    if norm > 0:
                        vector = vector / norm
                all_vectors.append(vector)
        
        return np.vstack(all_vectors) if all_vectors else np.array([])
    
    # ============================================================
    # FUNCTION 5: get_dimension (Returns vector size)
    # ============================================================
    def get_dimension(self) -> int:
        """Returns vector dimension (1536 for OpenAI)."""
        return self.dimension
    
    # ============================================================
    # FUNCTION 6: health_check (Check if working)
    # ============================================================
    def health_check(self) -> dict:
        """Returns health status."""
        return {
            "provider": "openai",
            "status": "healthy" if self.client else "unavailable",
            "dimension": self.dimension,
            "model": self.model
        }


# Singleton instance
embedding_generator = EmbeddingGenerator()


# ============================================================
# TEST BLOCK
# ============================================================
if __name__ == '__main__':
    print('\n' + '=' * 60)
    print('TESTING EMBEDDING GENERATOR (OpenAI)')
    print('=' * 60)
    
    gen = EmbeddingGenerator()
    
    # Health check
    print('\n1. Health Check:')
    print(f'   {gen.health_check()}')
    
    # Test encode_query
    print('\n2. Testing encode_query():')
    test_question = 'How to treat cassava disease?'
    vector = gen.encode_query(test_question)
    print(f'   Question: {test_question}')
    print(f'   Vector shape: {vector.shape}')
    print(f'   Expected: (1536,)')
    
    # Test encode_documents
    print('\n3. Testing encode_documents():')
    test_chunks = [
        'Cassava mosaic is caused by whiteflies.',
        'Remove infected plants to prevent spread.',
        'Use resistant cassava varieties.'
    ]
    vectors = gen.encode_documents(test_chunks)
    print(f'   Number of chunks: {len(test_chunks)}')
    print(f'   Vectors shape: {vectors.shape}')
    print(f'   Expected: (3, 1536)')
    
    # Check PDF files
    print('\n4. PDF Files Ready:')
    data_dir = Path(__file__).parent.parent / 'data'
    pdf_files = list(data_dir.glob('*.pdf')) if data_dir.exists() else []
    print(f'   Found {len(pdf_files)} PDF files in rag/data/')
    
    # Summary
    print('\n' + '=' * 60)
    print(' EMBEDDING GENERATOR WORKING!')
    print('=' * 60)
    print('\n Summary:')
    print(f'   Provider: OpenAI')
    print(f'   Status: Healthy')
    print(f'   Vector Dimension: 1536')
    print(f'   PDFs Ready: {len(pdf_files)}')
    print('\n Ready for Task 6.2 (Vector Database)')
    print('=' * 60)