"""Mock embedding provider for testing.

Produces deterministic, content-based embeddings using simple hashing.
No external service calls required.
"""
from __future__ import annotations

import hashlib
import math

from app.analysis.RAG.embeddings.base import EmbeddingProvider
from app.analysis.RAG.utils.logging import get_logger

logger = get_logger("embeddings.mock")


class MockEmbeddingProvider(EmbeddingProvider):
    """Deterministic mock embedding provider.
    
    Generates embeddings by hashing text content. The same text
    always produces the same embedding, making tests deterministic.
    """

    def __init__(self, dimension: int = 768):
        self._dimension = dimension
        logger.info("MockEmbeddingProvider initialized (dim=%d)", dimension)

    def embed_text(self, text: str) -> list[float]:
        return self._hash_to_vector(text)

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        return [self._hash_to_vector(t) for t in texts]

    def embed_query(self, query: str) -> list[float]:
        return self._hash_to_vector(query)

    @property
    def dimension(self) -> int:
        return self._dimension

    @property
    def model_name(self) -> str:
        return "mock-embedding"

    def _hash_to_vector(self, text: str) -> list[float]:
        """Convert text to a deterministic unit vector via SHA-256."""
        h = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # Expand hash to fill dimension
        expanded = h
        while len(expanded) < self._dimension * 2:
            expanded += hashlib.sha256(expanded.encode()).hexdigest()

        raw = [int(expanded[i * 2 : i * 2 + 2], 16) / 255.0 for i in range(self._dimension)]
        # L2 normalize
        norm = math.sqrt(sum(x * x for x in raw))
        if norm > 0:
            raw = [x / norm for x in raw]
        return raw
