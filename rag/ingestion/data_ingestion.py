'''Load documents from files'''

import os
import sys
from pathlib import Path
from typing import List, Optional
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    UnstructuredWordDocumentLoader
)
from langchain_core.documents import Document
sys.path.append(str(Path(__file__).parent.parent))
from config.loader import config
from logger.custom_logger import get_logger

#Get logger
logger = get_logger(__name__).logger

class DocumentLoader:
    '''
    Load documents from files using LangChain loaders.
    '''
    
    def __init__(self):
        '''Initialize the document loader.'''
        self.loaded_count = 0
        self.error_count = 0
        self.errors = [] # Stores error messages for debugging
        
        logger.info('DocumentLoader Initialized')
        
    def _get_loader_for_file(self, file_path: str):
        '''
        Get the appropriate loader for a file based on its extension.
        
        ARGS:
            file_path: Path to the file
        
        RETURNS:
            Loader instance or None if unsupported
        '''
        
        #splits "document.pdf" into ("document", ".pdf"), select .pdf
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext == '.pdf':
            logger.debug(f'Using PyPDFLoader for: {file_path}')
            return PyPDFLoader(file_path)
        
        # Text files - entire file becomes one Document
        elif ext == '.txt':
            logger.debug(f'Using TextLoader for: {file_path}')
            return TextLoader(file_path, encoding='utf-8')
        
        # Docx file
        elif ext == '.docx':
            logger.debug(f'Using UnstructuredWordDocumentLoader for: {file_path}')
            return UnstructuredWordDocumentLoader(file_path)
        
        # Unsupported file type
        else:
            logger.warning(f'Unsupported file type: {ext} for {file_path}')
            return None
        
        
    # Add metadata to documents
    def _add_metadata(self, documents: List[Document], file_path: str) -> List[Document]:
        '''
        Add source, filename, and file_type to each document's metadata.
        
        ARGS:
            documents: List of Document objects
            file_path: Source file path
        
        RETURNS:
            Documents with metadata added
        '''
        file_name = os.path.basename(file_path)
        file_type = os.path.splitext(file_path)[1].lower()
        
        for doc in documents:
            doc.metadata['source'] = file_path
            doc.metadata['filename'] = file_name
            doc.metadata['file_type'] = file_type
            
        return documents
    
    
    # Load a single file
    def load_file(self, file_path: str) -> List[Document]:
        '''
        Load a single file and return its documents with metadata.
        
        ARGS:
            file_path: Path to the file to load
        
        RETURNS:
            List of Document objects
        '''
        
        file_path = str(file_path)
        logger.info(f'Loading file: {os.path.basename(file_path)}')
        
        # Get the appropriate loader
        loader = self._get_loader_for_file(file_path)
        
        if loader is None:
            logger.warning(f'Skipping unsupported file: {file_path}')
            self.error_count += 1
            self.errors.append(f'Unsupported format: {file_path}')
            
            return []
        
        try:
            # Load documents
            documents = loader.load()
            
            #Add metadata
            documents = self._add_metadata(documents, file_path)
            
            # Update statistics
            self.loaded_count += len(documents)
            logger.info(f'Loaded: {os.path.basename(file_path)} ({len(documents)} pages)')
            
            return documents
        
        except Exception as e:
            logger.error(f'Error loading {file_path}: {e}')
            self.error_count += 1
            self.errors.append(f'Error loading {file_path}: {e}')
            
            return []
        
        
    # Load all PDFs from data directory
    def load_data_directory(self) -> List[Document]:
        '''
        Load all PDF files from the rag/data/ directory.
        
        RETURNS:
            List of all Document objects from all PDF files
        '''
        
        # Get data directory path
        data_dir = Path(__file__).parent.parent / 'data'
        logger.info(f'Loading documents from: {data_dir}')
        
        # Check if directory exist
        if not data_dir.exists():
            logger.warning(f'Data directory not found: {data_dir}')
            data_dir.mkdir(parents=True, exist_ok=True)
            return []
        
        # Get all pdf files
        pdf_files = list(data_dir.glob('*.pdf'))
        logger.info(f'Found {len(pdf_files)} PDF files')
        
        # Load each pdf
        all_documents = []
        for pdf_file in pdf_files:
            documents = self.load_file(str(pdf_file))
            all_documents.extend(documents)
            
        # Log summary
        logger.info(f'Total loaded: {len(all_documents)} documents from {len(pdf_files)} files')
        
        if self.error_count > 0:
            logger.warning(f'Errors: {self.error_count} files failed')
            
        return all_documents
    
    
    # Get loading statistics
    def get_stats(self) -> dict:
        '''Return loading statistics.'''
        
        return {
            'loaded_count': self.loaded_count,
            'error_count': self.error_count,
            'error': self.errors.copy()
        }
        
        
if __name__=='__main__':
    print('=' * 60)
    print('TESTING DOCUMENTLOADER CLASS')
    print('=' * 60)
    
    # Create loader
    loader = DocumentLoader()

    # Load all documents
    print(f'Loading documents from data directory...')
    documents = loader.load_data_directory()
    
    # Print results
    print('=' * 60)
    print('RESULTS')
    print('=' * 60)    
    print(f'Statistics: {loader.get_stats()}')
    print(f'Total documents loaded: {len(documents)}')

    # Show preview of first document
    if documents:
        print(f'\n First document preview:')
        print(f"    Filename: {documents[0].metadata.get('filename', 'Unknown')}")
        print(f"   Type: {documents[0].metadata.get('file_type', 'Unknown')}")
        print(f"    Content: {documents[0].page_content[:200]}....")
        
    else:
        print('\n   No documents loaded. Add PDF files to rag/data/')
        
        
    print('=' * 60)
    print('TEST COMPLETE')
    print('=' * 60) 