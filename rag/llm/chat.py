"""
FILE: rag/llm/chat.py - Uses ChromaDB directly for vector search
"""

import os
import sys
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from uuid import uuid4

sys.path.append(str(Path(__file__).parent.parent))
from logger.custom_logger import get_logger

logger = get_logger(__name__).logger

# Try to import ChromaDB
try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not installed")

# Try to import sentence-transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    EMBEDDINGS_AVAILABLE = True
except ImportError:
    EMBEDDINGS_AVAILABLE = False
    logger.warning("sentence-transformers not installed")


class FarmerChat:
    """Generate answers for farmers using ChromaDB vector search."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            logger.info('=' * 40)
            logger.info('CREATING FARMER CHAT')
            logger.info('=' * 40)
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        logger.info('Initializing Farmer Chat System...')
        
        self.session_histories = {}
        self.collection = None
        self.model = None
        
        # Initialize ChromaDB
        self._init_chromadb()
        
        self.is_ready = self.collection is not None
        logger.info(f'FARMER CHAT READY: {self.is_ready}')
    
    def _init_chromadb(self):
        """Initialize ChromaDB connection with vectors"""
        
        if not CHROMA_AVAILABLE:
            logger.error("ChromaDB not available - run: pip install chromadb")
            return
        
        # Find the correct chroma_db path
        possible_paths = [
            "/opt/render/project/src/rag/chroma_db",  # Render path
            "./chroma_db",  # Local relative
            "../chroma_db",  # Parent directory
            str(Path(__file__).parent.parent / "chroma_db"),  # Absolute from this file
        ]
        
        # Also check for any chroma_db directory
        for root, dirs, files in os.walk("."):
            if "chroma_db" in dirs:
                chroma_candidate = os.path.join(root, "chroma_db")
                if os.path.exists(os.path.join(chroma_candidate, "chroma.sqlite3")):
                    possible_paths.insert(0, chroma_candidate)
                    break
        
        chroma_path = None
        for path in possible_paths:
            if path and os.path.exists(path) and os.path.isdir(path):
                # Check if it has chroma.sqlite3
                if os.path.exists(os.path.join(path, "chroma.sqlite3")):
                    chroma_path = path
                    logger.info(f"✅ Found ChromaDB at: {chroma_path}")
                    break
        
        if not chroma_path:
            logger.error("❌ ChromaDB not found. Please ensure chroma_db folder is in the repository")
            return
        
        try:
            # Connect to ChromaDB
            self.client = chromadb.PersistentClient(
                path=chroma_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # List all collections
            collections = self.client.list_collections()
            logger.info(f"Available collections: {[c.name for c in collections]}")
            
            # Try to get the collection (your ingestion uses farm_data_openai)
            collection_name = "farm_data_openai"
            if collection_name in [c.name for c in collections]:
                self.collection = self.client.get_collection(collection_name)
                logger.info(f"✅ Loaded collection '{collection_name}' with {self.collection.count()} vectors")
            else:
                # Try to find any collection
                for c in collections:
                    self.collection = self.client.get_collection(c.name)
                    logger.info(f"✅ Loaded collection '{c.name}' with {self.collection.count()} vectors")
                    break
            
            # Initialize embedding model for queries
            if EMBEDDINGS_AVAILABLE and self.collection:
                self.model = SentenceTransformer('all-MiniLM-L6-v2')
                logger.info("✅ Embedding model loaded")
                
        except Exception as e:
            logger.error(f"❌ Failed to initialize ChromaDB: {e}")
            self.collection = None
    
    def _get_embedding(self, text: str):
        """Get embedding vector for text"""
        if self.model:
            return self.model.encode(text).tolist()
        return None
    
    def _search(self, question: str, top_k: int = 5) -> tuple:
        """Search for relevant chunks using vector similarity"""
        
        if not self.collection:
            logger.warning("No ChromaDB collection available")
            return '', []
        
        try:
            # Try embedding search first
            query_embedding = self._get_embedding(question)
            
            if query_embedding:
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    include=['documents', 'metadatas', 'distances']
                )
            else:
                # Fallback to text search
                results = self.collection.query(
                    query_texts=[question],
                    n_results=top_k,
                    include=['documents', 'metadatas', 'distances']
                )
            
            if not results['documents'] or not results['documents'][0]:
                logger.info("No results found")
                return '', []
            
            context_parts = []
            sources = []
            
            for i in range(len(results['documents'][0])):
                text = results['documents'][0][i]
                if not text or len(text.strip()) < 20:
                    continue
                
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                similarity = round(1 - min(distance, 1), 3)
                
                filename = metadata.get('filename', 'Unknown')
                page = metadata.get('page', 'N/A')
                
                # Truncate text for display
                display_text = text[:600] + "..." if len(text) > 600 else text
                
                context_parts.append(f'📄 From {filename} (page {page}):\n{display_text}\n')
                sources.append({
                    'filename': filename,
                    'page': str(page),
                    'relevance': similarity
                })
            
            context = '\n'.join(context_parts)
            logger.info(f"Found {len(sources)} relevant chunks")
            return context, sources
            
        except Exception as e:
            logger.error(f"Search error: {e}")
            return '', []
    
    def ask(self, question: str, session_id: str = None, top_k: int = 5) -> Dict[str, Any]:
        """Answer farmer's question using vector search"""
        
        if session_id is None:
            session_id = str(uuid4())
        
        if not question:
            return {'answer': 'Please ask a question.', 'sources': []}
        
        logger.info(f'Question: {question[:100]}')
        
        # Search ChromaDB
        context, sources = self._search(question, top_k)
        
        if context:
            # Build answer from search results
            answer = f"Based on your agricultural PDFs:\n\n{context}"
        else:
            answer = """I couldn't find specific information about that in your PDFs.

Please try asking about:
• Cassava diseases (Mosaic, Brown Streak)
• Rice production (Blast disease, planting)
• Maize farming (Rust, pest control)
• Tomato diseases (Late Blight, Early Blight)
• Pest control (Whiteflies, neem oil)
• Cassava varieties (TME 419)
• Apple diseases (Scab, Powdery Mildew)
• Potato diseases (Late Blight)"""
        
        # Save to history
        history = self.session_histories.get(session_id, [])
        history.append({'question': question, 'answer': answer})
        if len(history) > 10:
            history = history[-10:]
        self.session_histories[session_id] = history
        
        return {
            'answer': answer,
            'sources': sources[:3]
        }
    
    def clear_memory(self, session_id: str):
        if session_id in self.session_histories:
            self.session_histories[session_id] = []
        logger.info(f'Memory cleared')


# Create singleton instance
farmer_chat = FarmerChat()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("TESTING FARMER CHAT")
    print("=" * 50)
    
    if CHROMA_AVAILABLE:
        print(f"✅ ChromaDB available")
    else:
        print(f"❌ ChromaDB not available")
    
    if EMBEDDINGS_AVAILABLE:
        print(f"✅ Sentence-transformers available")
    else:
        print(f"❌ Sentence-transformers not available")
    
    chat = FarmerChat()
    
    if chat.is_ready:
        test_questions = [
            "How to treat cassava mosaic?",
            "What is TME 419?",
        ]
        
        for q in test_questions:
            print(f"\n📝 Q: {q}")
            result = chat.ask(q)
            print(f"✅ A: {result['answer'][:300]}...")
            if result['sources']:
                print(f"📚 Sources: {[s['filename'] for s in result['sources']]}")
    else:
        print("⚠️ FarmerChat not ready - ChromaDB not found")
        print("Make sure chroma_db folder is in the repository")
    
    print('\n✅ Test complete')