"""Embedding service with caching, retry, and rate-limit awareness.

Wraps any EmbeddingProvider with:
- LRU caching of embeddings
- Retry with exponential backoff
- Rate-limit awareness
- Batch processing
"""
from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from typing import Any

from app.analysis.RAG.config.settings import EmbeddingConfig
from app.analysis.RAG.embeddings.base import EmbeddingProvider
from app.analysis.RAG.utils.logging import get_logger

logger = get_logger("embeddings.service")


class EmbeddingService:
    """Wraps an EmbeddingProvider with caching, retry, and batching."""

    def __init__(
        self,
        provider: EmbeddingProvider,
        config: EmbeddingConfig | None = None,
    ):
        self._provider = provider
        self._config = config or EmbeddingConfig()
        self._cache: OrderedDict[str, list[float]] = OrderedDict()
        self._cache_max_size = 10000
        self._request_timestamps: list[float] = []

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text with caching."""
        cache_key = self._cache_key(text)
        cached = self._cache_get(cache_key)
        if cached is not None:
            return cached

        embedding = self._embed_with_retry(text)
        self._cache_put(cache_key, embedding)
        return embedding

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts, using cache where possible."""
        results: list[list[float] | None] = [None] * len(texts)
        uncached_indices: list[int] = []
        uncached_texts: list[str] = []

        # Check cache first
        for i, text in enumerate(texts):
            cache_key = self._cache_key(text)
            cached = self._cache_get(cache_key)
            if cached is not None:
                results[i] = cached
            else:
                uncached_indices.append(i)
                uncached_texts.append(text)

        # Process uncached texts in batches
        if uncached_texts:
            batch_size = self._config.batch_size
            for start in range(0, len(uncached_texts), batch_size):
                batch = uncached_texts[start : start + batch_size]
                self._wait_for_rate_limit()
                embeddings = self._provider.embed_batch(batch)
                for j, emb in enumerate(embeddings):
                    idx = uncached_indices[start + j]
                    results[idx] = emb
                    self._cache_put(self._cache_key(batch[j]), emb)

        return [r for r in results if r is not None]  # type: ignore

    def embed_query(self, query: str) -> list[float]:
        """Embed a query (no caching — queries are typically unique)."""
        return self._provider.embed_query(query)

    @property
    def dimension(self) -> int:
        return self._provider.dimension

    @property
    def model_name(self) -> str:
        return self._provider.model_name

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    def _embed_with_retry(self, text: str) -> list[float]:
        """Embed with retry and exponential backoff."""
        last_error: Exception | None = None
        for attempt in range(self._config.max_retries):
            try:
                self._wait_for_rate_limit()
                return self._provider.embed_text(text)
            except Exception as e:
                last_error = e
                delay = self._config.retry_delay * (2 ** attempt)
                logger.warning(
                    "Embedding attempt %d failed: %s. Retrying in %.1fs",
                    attempt + 1, e, delay,
                )
                time.sleep(delay)
        raise RuntimeError(
            f"Embedding failed after {self._config.max_retries} retries: {last_error}"
        )

    def _wait_for_rate_limit(self) -> None:
        """Simple rate limiter based on requests per minute."""
        if self._config.rate_limit_rpm <= 0:
            return
        now = time.monotonic()
        window = 60.0
        self._request_timestamps = [
            t for t in self._request_timestamps if now - t < window
        ]
        if len(self._request_timestamps) >= self._config.rate_limit_rpm:
            sleep_time = window - (now - self._request_timestamps[0]) + 0.1
            if sleep_time > 0:
                logger.debug("Rate limit reached, sleeping %.1fs", sleep_time)
                time.sleep(sleep_time)
        self._request_timestamps.append(time.monotonic())

    def _cache_key(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def _cache_get(self, key: str) -> list[float] | None:
        if not self._config.cache_enabled:
            return None
        if key in self._cache:
            self._cache.move_to_end(key)
            return self._cache[key]
        return None

    def _cache_put(self, key: str, value: list[float]) -> None:
        if not self._config.cache_enabled:
            return
        self._cache[key] = value
        self._cache.move_to_end(key)
        while len(self._cache) > self._cache_max_size:
            self._cache.popitem(last=False)
