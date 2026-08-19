"""Google Gemini embedding provider.

Uses the modern Google GenAI Python SDK (google-genai) with model gemini-embedding-2.
"""
from __future__ import annotations

import logging
import os
import time
from typing import Optional

try:
    from google import genai
    from google.genai import types
except ImportError:
    genai = None
    types = None

from app.analysis.RAG.embeddings.base import EmbeddingProvider

logger = logging.getLogger(__name__)

DEFAULT_GEMINI_EMBEDDING_MODEL = "gemini-embedding-2"
DEFAULT_EMBEDDING_DIMENSION = 768


class GeminiEmbeddingProvider(EmbeddingProvider):
    """
    Google Gemini Embedding Provider using google-genai SDK.
    Primary model: gemini-embedding-2 (dimension 768).
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = DEFAULT_GEMINI_EMBEDDING_MODEL,
        dimension: int = DEFAULT_EMBEDDING_DIMENSION,
        max_retries: int = 3,
        retry_delay: float = 1.0,
    ):
        self._model = model or os.environ.get("GEMINI_EMBEDDING_MODEL", DEFAULT_GEMINI_EMBEDDING_MODEL)
        self._dimension = dimension
        self._max_retries = max_retries
        self._retry_delay = retry_delay

        self._api_key = (
            api_key
            or os.environ.get("GEMINI_API_KEY")
            or os.environ.get("GOOGLE_API_KEY")
            or os.environ.get("LLM_API_KEY", "")
        )

        self._client = None
        if genai is not None and self._api_key and self._api_key not in ("mock_key", "your_gemini_api_key_here"):
            try:
                self._client = genai.Client(api_key=self._api_key)
            except Exception as e:
                logger.warning(f"Could not initialize GenAI client for embeddings: {e}")

    def _get_client(self):
        if self._client is None:
            if genai is None:
                raise ImportError("google-genai is not installed. Please install it using 'pip install google-genai'.")
            effective_key = (
                self._api_key
                or os.environ.get("GEMINI_API_KEY")
                or os.environ.get("GOOGLE_API_KEY")
                or os.environ.get("LLM_API_KEY", "")
            )
            if not effective_key or effective_key in ("mock_key", "your_gemini_api_key_here"):
                raise ValueError("Gemini API key is required when Gemini embedding functionality is enabled.")
            self._client = genai.Client(api_key=effective_key)
        return self._client

    def embed_text(self, text: str) -> list[float]:
        """Generate embedding for a single document text."""
        return self._embed_with_retry([text], task_type="RETRIEVAL_DOCUMENT")[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []
        return self._embed_with_retry(texts, task_type="RETRIEVAL_DOCUMENT")

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query."""
        return self._embed_with_retry([query], task_type="RETRIEVAL_QUERY")[0]

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    def _embed_with_retry(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        """Call GenAI embed_content API with retries and exponential backoff."""
        client = self._get_client()
        last_error = None

        config = None
        if types is not None:
            config = types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self._dimension if self._dimension else None,
            )

        for attempt in range(self._max_retries + 1):
            try:
                response = client.models.embed_content(
                    model=self._model,
                    contents=texts if len(texts) > 1 else texts[0],
                    config=config,
                )

                # Extract embedding vectors
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
                if attempt == self._max_retries:
                    logger.error(f"Failed to generate Gemini embeddings after {self._max_retries} retries: {e}")
                    raise

                delay = self._retry_delay * (2 ** attempt)
                logger.warning(f"Embedding attempt {attempt + 1} failed, retrying in {delay}s: {e}")
                time.sleep(delay)

        raise RuntimeError(f"Embedding failed: {last_error}")
