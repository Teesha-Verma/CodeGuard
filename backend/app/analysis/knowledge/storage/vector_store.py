import logging
import os
from typing import Any

from app.analysis.knowledge.constants import DEFAULT_EMBEDDING_DIMENSION, DEFAULT_TOP_K

logger = logging.getLogger(__name__)

class FAISSVectorStore:
    """
    FAISS-based vector store for embedding similarity search.
    
    Responsibilities:
    - Create and manage FAISS indices
    - Insert embedding vectors
    - Perform similarity search
    - Persist indices to disk
    - Load indices from disk
    
    No business logic — pure vector operations.
    """
    
    def __init__(self, dimension: int = DEFAULT_EMBEDDING_DIMENSION, index_path: str | None = None):
        self._dimension = dimension
        self._index_path = index_path
        self._index: Any = None  # faiss.IndexFlatIP (inner product for cosine similarity)
        self._id_map: list[str] = []  # Maps FAISS internal indices to chunk_ids
        self._initialize_index()
    
    def _initialize_index(self) -> None:
        try:
            import faiss
        except ImportError:
            logger.error("faiss is not installed. Please install faiss-cpu or faiss-gpu.")
            raise
        
        # Create IndexFlatIP for cosine similarity (vectors must be L2-normalized)
        self._index = faiss.IndexFlatIP(self._dimension)
    
    def add_embeddings(self, chunk_ids: list[str], embeddings: list[list[float]]) -> int:
        """Add embeddings to the index. Returns number added."""
        if not chunk_ids or not embeddings:
            return 0
        if len(chunk_ids) != len(embeddings):
            raise ValueError("Length of chunk_ids must match length of embeddings.")
            
        try:
            import faiss
            import numpy as np
        except ImportError:
            logger.error("faiss and numpy are required. Install faiss-cpu and numpy.")
            raise
            
        vecs = np.array(embeddings, dtype=np.float32)
        # L2 normalize vectors
        faiss.normalize_L2(vecs)
        
        self._index.add(vecs)
        self._id_map.extend(chunk_ids)
        return len(chunk_ids)
    
    def search(self, query_embedding: list[float], top_k: int = DEFAULT_TOP_K) -> list[tuple[str, float]]:
        """Search for similar vectors. Returns list of (chunk_id, similarity_score)."""
        if self._index is None or self._index.ntotal == 0:
            return []
            
        try:
            import faiss
            import numpy as np
        except ImportError:
            logger.error("faiss and numpy are required. Install faiss-cpu and numpy.")
            raise
            
        vec = np.array([query_embedding], dtype=np.float32)
        faiss.normalize_L2(vec)
        
        distances, indices = self._index.search(vec, top_k)
        
        results = []
        for i, idx in enumerate(indices[0]):
            if 0 <= idx < len(self._id_map):
                results.append((self._id_map[idx], float(distances[0][i])))
                
        return results
    
    def save(self, path: str | None = None) -> str:
        """Save index to disk. Returns the path."""
        try:
            import faiss
        except ImportError:
            logger.error("faiss is not installed.")
            raise
            
        save_path = path or self._index_path
        if not save_path:
            raise ValueError("No path provided to save index.")
            
        faiss.write_index(self._index, save_path)
        return save_path
    
    def load(self, path: str | None = None) -> None:
        """Load index from disk."""
        try:
            import faiss
        except ImportError:
            logger.error("faiss is not installed.")
            raise
            
        load_path = path or self._index_path
        if not load_path:
            raise ValueError("No path provided to load index.")
            
        self._index = faiss.read_index(load_path)
    
    @property
    def size(self) -> int:
        """Number of vectors in the index."""
        if self._index:
            return self._index.ntotal
        return 0
    
    def clear(self) -> None:
        """Reset the index."""
        self._id_map = []
        self._initialize_index()
