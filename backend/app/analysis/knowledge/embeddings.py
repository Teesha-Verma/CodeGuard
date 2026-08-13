import logging
import os
import time
from abc import ABC, abstractmethod
from typing import List, Optional

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from app.analysis.knowledge.constants import (
    DEFAULT_EMBEDDING_MODEL,
    MAX_EMBEDDING_BATCH_SIZE
)
from app.analysis.knowledge.models import EmbeddingResult

logger = logging.getLogger(__name__)

class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""
    
    @abstractmethod
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass
    
    @abstractmethod
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of texts."""
        pass
    
    @abstractmethod
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a query (may use different task type)."""
        pass
    
    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the embedding dimension."""
        pass
    
    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the model name."""
        pass

class GoogleGeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini embedding provider using google.generativeai.
    
    Uses models/text-embedding-004 by default.
    Supports batch embedding with configurable batch size.
    Implements retry logic for transient errors.
    """
    
    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        api_key: Optional[str] = None,
        max_batch_size: int = MAX_EMBEDDING_BATCH_SIZE,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        if genai is None:
            raise ImportError("google.generativeai is not installed. Please install it to use GoogleGeminiEmbeddingProvider.")
            
        self._model = model
        self.max_batch_size = max_batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        # Configure genai
        api_key_to_use = api_key or os.environ.get("GOOGLE_API_KEY")
        if not api_key_to_use:
            raise ValueError("API key must be provided or GOOGLE_API_KEY environment variable must be set.")
            
        genai.configure(api_key=api_key_to_use)
        
        # Standard dimension for gemini text-embedding-004
        self._dimension = 768
        
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single document."""
        logger.debug(f"Embedding single text with model {self._model}")
        return self._embed_with_retry(text, task_type="RETRIEVAL_DOCUMENT")
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of documents."""
        logger.debug(f"Embedding batch of {len(texts)} texts")
        all_embeddings = []
        
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_result = self._embed_with_retry(batch, task_type="RETRIEVAL_DOCUMENT")
            
            # genai returns single embedding list or list of lists
            if isinstance(batch_result[0], list):
                all_embeddings.extend(batch_result)
            else:
                all_embeddings.append(batch_result)
                
        return all_embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        logger.debug(f"Embedding query with model {self._model}")
        return self._embed_with_retry(query, task_type="RETRIEVAL_QUERY")
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return self._model

    def _embed_with_retry(self, content, task_type: str, retries: int = 0) -> any:
        """Helper to invoke genai embedding API with retries and exponential backoff."""
        for attempt in range(self.max_retries + 1):
            try:
                result = genai.embed_content(
                    model=self._model,
                    content=content,
                    task_type=task_type
                )
                return result['embedding']
            except Exception as e:
                if attempt == self.max_retries:
                    logger.error(f"Failed to embed content after {self.max_retries} retries: {e}")
                    raise
                
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(f"Embedding attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
