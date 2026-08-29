import logging
import os
import time
from abc import ABC, abstractmethod
from typing import List, Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.analysis.knowledge.constants import (
    DEFAULT_EMBEDDING_MODEL,
    MAX_EMBEDDING_BATCH_SIZE,
    DEFAULT_EMBEDDING_DIMENSION,
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
    Google Gemini embedding provider using google-genai SDK.
    
    Uses gemini-embedding-2 by default.
    Supports batch embedding with configurable batch size.
    Implements retry logic with exponential backoff for transient errors.
    """
    
    def __init__(
        self,
        model: str = DEFAULT_EMBEDDING_MODEL,
        api_key: Optional[str] = None,
        max_batch_size: int = MAX_EMBEDDING_BATCH_SIZE,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self._model = model
        self.max_batch_size = max_batch_size
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self._dimension = DEFAULT_EMBEDDING_DIMENSION
        
        self._api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("LLM_API_KEY")
        )
        
        self._client = None
        if genai is not None and self._api_key and self._api_key not in ("mock_key", "your_gemini_api_key_here"):
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client: {e}")

    def _get_client(self):
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai is not installed. Please install it to use GoogleGeminiEmbeddingProvider.")
            effective_key = (
                self._api_key
                or os.environ.get("GEMINI_API_KEY")
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("LLM_API_KEY")
            )
            if not effective_key or effective_key in ("mock_key", "your_gemini_api_key_here"):
                raise ValueError("Gemini API key is required when Gemini embedding functionality is enabled.")
            self._client = genai.Client(api_key=effective_key)
        return self._client
        
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding for a single document."""
        logger.debug(f"Embedding single text with model {self._model}")
        return self._embed_with_retry([text], task_type="RETRIEVAL_DOCUMENT")[0]
    
    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a batch of documents."""
        logger.debug(f"Embedding batch of {len(texts)} texts")
        all_embeddings = []
        
        for i in range(0, len(texts), self.max_batch_size):
            batch = texts[i:i + self.max_batch_size]
            batch_result = self._embed_with_retry(batch, task_type="RETRIEVAL_DOCUMENT")
            all_embeddings.extend(batch_result)
                
        return all_embeddings
    
    def embed_query(self, query: str) -> List[float]:
        """Generate embedding for a search query."""
        logger.debug(f"Embedding query with model {self._model}")
        return self._embed_with_retry([query], task_type="RETRIEVAL_QUERY")[0]
    
    @property
    def dimension(self) -> int:
        return self._dimension
    
    @property
    def model_name(self) -> str:
        return self._model

    def _embed_with_retry(self, texts: List[str], task_type: str = "RETRIEVAL_DOCUMENT") -> List[List[float]]:
        """Helper to invoke genai embedding API with retries and exponential backoff."""
        client = self._get_client()
        last_error = None
        
        config = None
        if types is not None:
            config = types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self._dimension,
            )
        
        for attempt in range(self.max_retries + 1):
            try:
                response = client.models.embed_content(
                    model=self._model,
                    contents=texts if len(texts) > 1 else texts[0],
                    config=config,
                )
                
                if hasattr(response, "embeddings") and response.embeddings:
                    embeddings = []
                    for emb in response.embeddings:
                        if hasattr(emb, "values"):
                            embeddings.append(list(emb.values))
                        elif isinstance(emb, list):
                            embeddings.append(emb)
                    return embeddings
                elif hasattr(response, "embedding") and response.embedding:
                    if hasattr(response.embedding, "values"):
                        return [list(response.embedding.values)]
                    return [response.embedding]
                    
                raise ValueError("Unexpected response format from Gemini embedding API")
                
            except Exception as e:
                last_error = e
                if attempt == self.max_retries:
                    logger.error(f"Failed to embed content after {self.max_retries} retries: {e}")
                    raise
                
                delay = self.retry_delay * (2 ** attempt)
                logger.warning(f"Embedding attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)
                
        raise RuntimeError(f"Embedding failed: {last_error}")
