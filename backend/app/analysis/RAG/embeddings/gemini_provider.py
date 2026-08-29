"""Google Gemini embedding provider.

Uses the modern Google GenAI Python SDK (google-genai) with model gemini-embedding-2.
"""
from __future__ import annotations

import logging
import os
import random
import time
from typing import Optional, Set, Dict

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
        max_retries: int = 2,
        retry_delay: float = 1.0,
    ):
        self._model = model or os.environ.get("GEMINI_EMBEDDING_MODEL", DEFAULT_GEMINI_EMBEDDING_MODEL)
        self._dimension = dimension
        self._max_retries = max(1, min(max_retries, 2))
        self._retry_delay = retry_delay
        self._exhausted_models: Set[str] = set()
        self._query_cache: Dict[str, list[float]] = {}

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
        return self._embed_single(text, task_type="RETRIEVAL_DOCUMENT")

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for a batch of texts."""
        if not texts:
            return []
        all_embeddings: list[list[float]] = []
        for i, text in enumerate(texts):
            emb = self._embed_single(text, task_type="RETRIEVAL_DOCUMENT")
            all_embeddings.append(emb)
            if i + 1 < len(texts):
                time.sleep(0.05)  # Gentle pacing between embedding calls
        return all_embeddings

    def embed_query(self, query: str) -> list[float]:
        """Generate embedding for a search query with in-memory deduplication."""
        query_key = query.strip()
        if query_key in self._query_cache:
            return list(self._query_cache[query_key])

        emb = self._embed_single(query, task_type="RETRIEVAL_QUERY")
        if emb:
            self._query_cache[query_key] = emb
        return emb

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return self._model

    def _embed_single(self, text: str, task_type: str = "RETRIEVAL_DOCUMENT") -> list[float]:
        """Call GenAI embed_content API with quota awareness and model fallback."""
        client = self._get_client()
        last_error = None

        config = None
        if types is not None:
            config = types.EmbedContentConfig(
                task_type=task_type,
                output_dimensionality=self._dimension if self._dimension else None,
            )

        candidate_models = [self._model]
        if "gemini-embedding-001" not in candidate_models:
            candidate_models.append("gemini-embedding-001")

        for current_model in candidate_models:
            if current_model in self._exhausted_models:
                continue

            for attempt in range(1, self._max_retries + 1):
                try:
                    response = client.models.embed_content(
                        model=current_model,
                        contents=text,
                        config=config,
                    )

                    # Extract embedding vector
                    if hasattr(response, "embeddings") and response.embeddings:
                        first = response.embeddings[0]
                        if hasattr(first, "values"):
                            return list(first.values)
                        elif isinstance(first, list):
                            return list(first)
                    elif hasattr(response, "embedding") and response.embedding:
                        if hasattr(response.embedding, "values"):
                            return list(response.embedding.values)
                        return list(response.embedding)

                    raise ValueError("Unexpected response format from Gemini embedding API")

                except Exception as e:
                    last_error = e
                    err_str = str(e).lower()
                    is_daily_quota = any(
                        term in err_str for term in [
                            "embedcontentrequestsperday", "requests_per_day", "daily", "perday", "dayperproject"
                        ]
                    )
                    is_rpm_rate_limit = any(
                        term in err_str for term in [
                            "embedcontentrequestsperminute", "requests_per_minute", "perminute"
                        ]
                    ) or ("429" in err_str and not is_daily_quota)

                    if is_daily_quota:
                        self._exhausted_models.add(current_model)
                        logger.warning(
                            f"Gemini embedding daily quota exhausted for model {current_model}; switching to next fallback."
                        )
                        break  # Immediately try next candidate embedding model

                    if is_rpm_rate_limit:
                        if attempt < self._max_retries:
                            delay = min(3.0, self._retry_delay * (1.5 ** attempt) + random.uniform(0.1, 0.3))
                            logger.info(
                                f"Embedding rate limit on {current_model} (attempt {attempt}); retrying in {delay:.1f}s."
                            )
                            time.sleep(delay)
                            continue
                        else:
                            break

                    # Other transient errors
                    if attempt < self._max_retries:
                        delay = self._retry_delay * attempt
                        time.sleep(delay)
                        continue
                    break

        raise RuntimeError(f"Embedding failed across all candidate models: {last_error}")
