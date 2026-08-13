import hashlib
import logging
import time
from typing import Any

from app.analysis.knowledge.constants import DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD
from app.analysis.knowledge.models import (
    KnowledgeChunk, RetrievalRequest, RetrievalResult, RetrievedContext
)
from app.analysis.knowledge.embeddings import EmbeddingProvider
from app.analysis.knowledge.storage.vector_store import FAISSVectorStore
from app.analysis.knowledge.storage.cache import KnowledgeCache

logger = logging.getLogger(__name__)

class SemanticRetriever:
    """
    Semantic retrieval engine using embeddings and FAISS.
    
    Pipeline:
    1. Generate query embedding
    2. FAISS similarity search
    3. Map results to KnowledgeChunks
    4. Apply filters (category, tags, threshold)
    5. Return RetrievalResult objects
    """
    
    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: FAISSVectorStore,
        chunk_store: dict[str, KnowledgeChunk] | None = None,
        cache: KnowledgeCache | None = None,
    ):
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._chunk_store: dict[str, KnowledgeChunk] = chunk_store if chunk_store is not None else {}
        self._cache = cache
    
    def retrieve(self, request: RetrievalRequest) -> list[RetrievalResult]:
        """Execute semantic retrieval for the given request."""
        start_time = time.monotonic()
        
        # 1. Check cache
        cache_key = self._build_cache_key(request)
        if self._cache:
            cached_results = self._cache.get(cache_key)
            if cached_results:
                logger.debug(f"Cache hit for query: {request.query}")
                return cached_results

        try:
            # 2. Generate query embedding
            query_embedding = self._embedding_provider.embed_query(request.query)
            
            # 3. Search vector store
            top_k = getattr(request, 'top_k', DEFAULT_TOP_K)
            search_k = top_k * 2 
            raw_results = self._vector_store.search(query_embedding, top_k=search_k)
            
            # 4. Map to chunks and 5, 6 Apply filters
            threshold = getattr(request, 'similarity_threshold', DEFAULT_SIMILARITY_THRESHOLD)
            filtered_chunks = self._apply_filters(
                results=raw_results,
                categories=getattr(request, 'categories', None),
                tags=getattr(request, 'tags', None),
                threshold=threshold,
            )
            
            # 7. Build RetrievalResult objects
            final_results = []
            for chunk, score in filtered_chunks[:top_k]:
                result = RetrievalResult(
                    chunk=chunk,
                    similarity_score=score,
                    final_score=score,
                )
                final_results.append(result)
            
            # 8. Cache results
            if self._cache:
                self._cache.put(cache_key, final_results)
                
            elapsed = time.monotonic() - start_time
            logger.info(f"Retrieved {len(final_results)} results for query '{request.query}' in {elapsed:.3f}s")
            
            return final_results
            
        except Exception as e:
            logger.error(f"Error during semantic retrieval: {e}")
            raise
    
    def index_chunks(self, chunks: list[KnowledgeChunk], embeddings: list[list[float]]) -> int:
        """Index chunks and their embeddings for later retrieval."""
        if len(chunks) != len(embeddings):
            raise ValueError("Number of chunks must match number of embeddings")
            
        try:
            for chunk in chunks:
                chunk_id = getattr(chunk, 'chunk_id', str(id(chunk)))
                self._chunk_store[chunk_id] = chunk
            
            chunk_ids = [c.chunk_id for c in chunks]
            self._vector_store.add_embeddings(chunk_ids, embeddings)
            
            logger.info(f"Successfully indexed {len(chunks)} chunks")
            return len(chunks)
        except Exception as e:
            logger.error(f"Error indexing chunks: {e}")
            raise
    
    def _apply_filters(
        self,
        results: list[tuple[str, float]],
        categories: list | None,
        tags: list[str] | None,
        threshold: float,
    ) -> list[tuple[KnowledgeChunk, float]]:
        """Apply category, tag, and threshold filters."""
        filtered = []
        for chunk_id, score in results:
            if score < threshold:
                continue
                
            chunk = self._chunk_store.get(chunk_id)
            if not chunk:
                logger.warning(f"Chunk {chunk_id} not found in store")
                continue
                
            if categories and getattr(chunk, 'category', None) not in categories:
                continue
                
            if tags:
                chunk_tags = set(getattr(chunk, 'tags', []))
                if not any(tag in chunk_tags for tag in tags):
                    continue
                    
            filtered.append((chunk, score))
            
        return filtered
    
    def _build_cache_key(self, request: RetrievalRequest) -> str:
        """Build deterministic cache key from request."""
        tags = getattr(request, 'tags', None)
        cats = getattr(request, 'categories', None)
        
        key_parts = [
            getattr(request, 'query', ""),
            str(getattr(request, 'top_k', DEFAULT_TOP_K)),
            str(sorted(cats) if cats else "None"),
            str(sorted(tags) if tags else "None"),
            str(getattr(request, 'similarity_threshold', DEFAULT_SIMILARITY_THRESHOLD))
        ]
        key_str = "|".join(key_parts)
        return hashlib.md5(key_str.encode("utf-8")).hexdigest()
