''' 
Load PDFs → Split → Embed → Store in ChromaDB 
    1. Reads all PDFs from rag/data/ using DocumentLoader
    2. Splits into chunks using DataSplitter  
    3. Converts to vectors using OpenAI
    4. Stores in ChromaDB for searching
'''

import sys
import uuid
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from logger.custom_logger import get_logger
from ingestion.data_ingestion import DocumentLoader
from ingestion.data_splitter import DataSplitter
from embeddings.embedding_generator import embedding_generator
from vector_store.chroma_store import vector_db

logger = get_logger(__name__).logger

# Main function
def ingest_all():
    '''
    Load PDFs → Split → Embed → Store
    '''

    print('=' * 60)
    print('   INGESTING PDFs INTO VECTOR DATABASE')
    print('=' * 60)
    
    # Load PDFs
    print('\n   Loading PDFs from rag/data/...')
    
    loader = DocumentLoader()
    documents = loader.load_data_directory()
    
    if not documents:
        print('   No PDFs found. Add PDF files to rag/data/ folder')
        return False
    
    print(f'   Loaded {len(documents)} pages from {loader.loaded_count} files')
    
    # Split into chunks
    print('\n   Splitting into chunks...')
    
    splitter = DataSplitter()
    chunks = splitter.split_documents(documents)
    
    print(f'   Created {len(chunks)} chunks')
    print(f'   Chunk size: {splitter.chunk_size} chars')
    print(f'   Overlap: {splitter.chunk_overlap} chars')
    
    # Convert to vectors
    print('\n   Converting chunks to vectors...')

    # Extract text from chunks
    texts = [chunk.page_content for chunk in chunks]
    
    # Convert to vectors using OpenAI
    vectors = embedding_generator.encode_documents(texts)
    
    print(f'   Generated {vectors.shape[0]} vectors')
    print(f'   Each vector: {vectors.shape[1]} dimensions')
    
    # Prepare metadata and IDs
    print('Preparing metadata...')
    
    metadatas = []
    ids = []
    
    for i, chunk in enumerate(chunks):
        # Extract metadata from chunk
        metadata = {
            'filename': chunk.metadata.get('filename', 'Unknown'),
            'page': chunk.metadata.get('page', 1),
            'source': chunk.metadata.get('source', 'Unknown'),
            'chunk_index': i,
            'text': chunk.page_content
        }
        metadatas.append(metadata)
        
        # Create unique ID for each chunk
        ids.append(str(uuid.uuid4()))
        
        print(f'   Prepared {len(metadatas)} metadata entries')
        
        # Store in ChromaDB
        print('\n   Storing vectors in ChromaDB...')
        
        # Check if database is ready
        if vector_db.table is None:
            print('   Database not ready. Check ChromaDB installation')
            return False
        
    #Store vectors
    vector_db.store_vectors(vectors, metadatas, ids)
        
        
    # Summary
    print('=' * 60)
    print('INGESTION COMPLETE!')
    print('=' * 60)
    print(f'\n Summary:')
    print(f'    PDF files: {loader.loaded_count}')
    print(f'    Pages loaded: {len(documents)}')
    print(f'    Chunks created: {len(chunks)}')
    print(f'    Vector stored: {vector_db.count()}')
    print(f'    Database table: {vector_db.table_name}')
    print('\n   Farmers can now search your PDFs!')
    print('=' * 60)
        
    return True
    
    
if __name__=='__main__':
    ingest_all()