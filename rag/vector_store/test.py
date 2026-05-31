import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from rag.vector_store.chroma_store import VectorDatabase

db = VectorDatabase()
print(f"Vectors in database: {db.count()}")