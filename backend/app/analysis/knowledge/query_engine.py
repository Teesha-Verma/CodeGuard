import logging
import time
from typing import Any

from app.analysis.knowledge.models import (
    RetrievalRequest, RetrievedContext, RepositoryContext
)
from app.analysis.knowledge.constants import DEFAULT_TOP_K, DEFAULT_SIMILARITY_THRESHOLD
from app.analysis.knowledge.retrievers import SemanticRetriever
from app.analysis.knowledge.reranker import RerankerStrategy, WeightedReranker
from app.analysis.knowledge.repository_index import RepositoryIndex

logger = logging.getLogger(__name__)

class KnowledgeQueryEngine:
    """
    Orchestration layer for knowledge retrieval.
    
    Pipeline:
    1. Resolve repository context from RepositoryIndex
    2. Execute semantic retrieval
    3. Apply reranking
    4. Build final RetrievedContext
    
    This engine does NOT:
    - Call Gemini or any LLM
    - Generate prompts
    - Perform reasoning
    """
    
    def __init__(
        self,
        retriever: SemanticRetriever,
        reranker: RerankerStrategy | None = None,
        repository_index: RepositoryIndex | None = None,
    ):
        self._retriever = retriever
        self._reranker = reranker or WeightedReranker()
        self._repository_index = repository_index or RepositoryIndex()
    
    def query(
        self,
        query: str,
        top_k: int | None = None,
        categories: list | None = None,
        tags: list[str] | None = None,
        repository_url: str | None = None,
        similarity_threshold: float | None = None,
    ) -> RetrievedContext:
        """Execute a knowledge retrieval query."""
        start_time = time.monotonic()
        
        try:
            # 1. Resolve repository context
            repo_context = None
            if repository_url:
                repo_context = self._repository_index.get_context(repository_url)
            
            # 2. Build RetrievalRequest
            request = RetrievalRequest(
                query=query,
                top_k=top_k or DEFAULT_TOP_K,
                categories=categories,
                tags=tags,
                similarity_threshold=similarity_threshold or DEFAULT_SIMILARITY_THRESHOLD,
                repository_context=repo_context,
            )
            
            # 3. Retrieve
            results = self._retriever.retrieve(request)
            
            # 4. Rerank
            reranked = self._reranker.rerank(results, context=repo_context)
            
            # 5. Build RetrievedContext
            elapsed_ms = (time.monotonic() - start_time) * 1000
            
            context = RetrievedContext(
                query=query,
                results=reranked,
                total_results=len(reranked),
                repository_context=repo_context,
                retrieval_time_ms=elapsed_ms,
                metadata={
                    "top_k": top_k or DEFAULT_TOP_K,
                    "categories": [c.value for c in categories] if categories else None,
                }
            )
            
            logger.info(f"Query completed in {elapsed_ms:.2f}ms, {len(reranked)} results found")
            return context
            
        except Exception as e:
            logger.error(f"Error during query execution: {e}")
            raise
    
    def register_repository(self, context: RepositoryContext) -> None:
        """Register repository context for future queries."""
        try:
            self._repository_index.index_repository(context)
        except Exception as e:
            logger.error(f"Failed to register repository: {e}")
            raise
