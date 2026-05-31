import sys
from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Optional, Dict, Any

sys.path.append(str(Path(__file__).parent.parent))
from logger.custom_logger import get_logger
from config.loader import config
from ingestion.data_ingestion import DocumentLoader

# Get logger for this module
logger = get_logger(__name__).logger

# DATA SPLITTER CLASS
class DataSplitter:
    '''
    Split documents into smaller chunks for embedding and retrieval.
    '''
    
    def __init__(self, chunk_size: Optional[int]=None, chunk_overlap: Optional[int] = None):
        '''Initialize the text splitter with chunk size and overlap from config.'''

        try:
            # Get values from config if not provided
            if chunk_size is None:
                self.chunk_size = config.get('chunking', {}).get('chunk_size', 500)
                
            else:
                self.chunk_size = chunk_size
                
            if chunk_overlap is None:
                self.chunk_overlap = config.get('chunking', {}).get('chunk_overlap', 50)
            
            else:
                self.chunk_overlap = chunk_overlap
                
            # Get separators from config if available
            separators = config.get('chunking', {}).get('separators', ['\n\n', '\n', '. ', ' ', ''])
            
            # Initialize counter for number of chunks created
            self.chunk_count = 0
            
            # Create the LangChain text splitter
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=separators,
            )
        
        except Exception as e:
            logger.error(f'Failed to initialize DataSplitter {e}')
            # Fallback to defaults
            self.chunk_size = 500
            self.chunk_overlap = 50
            self.chunk_count = 0
            self.splitter = RecursiveCharacterTextSplitter(
                chunk_size=500,
                chunk_overlap=50,
                length_function=len,
                separators=['\n\n', '\n', '. ', ' ', '']
            )
            
            logger.warning('Using fallback defaults for DataSplitter')
            
    
    # Split list of documents
    def split_documents(self, documents: List[Document]) -> List[Document]:
        '''
        Split a list of documents into smaller chunks.
        
        ARGS:
            documents (List[Document]): List of LangChain Document objects
        
        RETURNS:
            List[Document]: List of chunked Document objects
        '''
        
        if not documents:
            logger.warning('No documents provided to split')
            return []
        
        try:
            logger.info(f'Splitting {len(documents)} documents into chunks...')
            
            original_count = len(documents)
            
            chunks = self.splitter.split_documents(documents)
            
            self.chunk_count = len(chunks)
            
            logger.info(f'Create {len(chunks)} chunks from {original_count} documents')
            logger.info(f'Average chunk size: {self.chunk_size} characters')
            logger.info(f'Chunk overlap: {self.chunk_overlap} characters')
            
            return chunks
        
        except Exception as e:
            logger.error(f'Failed to split documents: {e}')
            return []
        
        
    # Split single document
    def split_document(self, document: Document) -> List[Document]:
        '''
        Split a single document into chunks
        ARGS:
            document (Document): LangChain Document object to split
        
        RETURNS:
            List[Document]: List of chunked Document objects
        '''
        
        if document is None:
            logger.warning('No document provided to split')
            return []
        
        try:
            logger.debug(f"Splitting document: {document.metadata.get('filename', 'Unknown')}")
            
            chunks = self.splitter.split_documents([document])
            self.chunk_count += len(chunks)
            return chunks
        
        except Exception as e:
            logger.error(f'Failed to split document: {e}')
            return []
        
        
    # Split single text string
    def split_text(self, text: str, metadata: Optional[Dict[str, Any]] = None) -> List[Document]:
        '''
        Split a single text string into Document chunks.
        
        ARGS:
            text (str): The text to split
            metadata (dict): Optional metadata to attach to chunks
        
        RETURNS:
            List[Document]: List of chunked Document objects
        '''
        
        if not text:
            logger.warning('No text provided to split')
            return []
        
        if metadata is None:
            metadata = {}
            
        try:
            logger.debug(f'Splitting text of length {len(text)} characters')
            
            # Split the text into strings
            text_chunks = self.splitter.split_text(text)
            
            # Convert to Document objects with metadata
            documents = []
            
            for i, chunk_text in enumerate(text_chunks):
                chunk_metadata = metadata.copy()
                chunk_metadata['chunk_index'] = i
                chunk_metadata['chunk_total'] = len(text_chunks)
                documents.append(Document(page_content=chunk_text, metadata=chunk_metadata))
                
            self.chunk_count += len(documents)
            logger.debug(f'Created {len(documents)} chunks from text')
            
            return documents
        
        except Exception as e:
            logger.error(f'Failed to split text: {e}')
            return []
        
        
    # Get statistics
    def get_chunk_count(self) -> int:
        '''Get the total number of chunks created
        '''
        
        return self.chunk_count
    
    
    # Detailed statistics
    def get_stats(self) -> dict:
        '''Get detailed splitting statistics.'''
        
        return {
            'chunk_size': self.chunk_size,
            'chunk_overlap': self.chunk_overlap,
            'chunk_count': self.chunk_count
        }
        
    # Reset counter
    def reset_stats(self):
        '''Reset the chunk counter'''
        self.chunk_count = 0
        logger.debug('Chunk counter reset')
        
        
if __name__=='__main__':
    print('=' * 60)
    print('TESTING DATA SPLITTER WITH REAL PDF FILES')
    print('=' * 60)
    
    try:
        logger.info('Loading documents from data directory...')
        loader = DocumentLoader()
        documents = loader.load_data_directory()
        
        if not documents:
            print('\nNo documents loaded. Add PDF files to rag/data/')
            print('=' * 60)
            print('TEST COMPLETE')
            print('=' * 60)
            
        print(f'\nLoaded {len(documents)} document pages from {loader.loaded_count} files')
        print(f'Error: {loader.error_count}')
        
        logger.info('Splitting documents into chunks...')
        splitter = DataSplitter()
        chunks = splitter.split_documents(documents)
        
        print('\n' + '=' * 60)
        print('RESULTS')
        print('=' * 60)
        print(f'Statistics: {splitter.get_stats()}')
        print(f'Total chunks created: {len(chunks)}')
        
        # Show preview of first chunk
        if chunks:
            print(f'\nFirst chunk preview:')
            print(f"    Filename: {chunks[0].metadata.get('filename', 'Unknown')}")
            print(f"    Page: {chunks[0].metadata.get('page', 'N/A')}")
            print(f'    Length: {len(chunks[0].page_content)} characters')
            print(f'    Content: {chunks[0].page_content[:400]}...')
            
        # Show summary of chunks per file
        print(f'\n Chunks per file:')
        file_chunk_counts = {}
        for chunk in chunks:
            filename = chunk.metadata.get('filename', 'Unknown')
            file_chunk_counts[filename] = file_chunk_counts.get(filename, 0) + 1
            
        for filename, count in list(file_chunk_counts.items())[:5]:
            print(f'    -{filename}: {count} chunks')
        
        if len(file_chunk_counts) > 5:
            print(f'    ... and {len(file_chunk_counts) - 5} more files')
        
    
    except Exception as e:
        print(f'Could not import DocumentLoader: {e}')
        
        print('\n' + '=' * 60)
        print('TEST COMPLETE')
        print('=' * 60)