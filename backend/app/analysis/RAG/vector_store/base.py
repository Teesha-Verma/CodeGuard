"""Abstract vector store interface.

Provider-agnostic abstraction for vector storage.
FAISS, pgvector, or Chroma can be swapped by implementing this interface.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from app.analysis.RAG.models.documents import EmbeddingDocument, SearchResult


class VectorStore(ABC):
    """Abstract base class for vector storage."""

    @abstractmethod
    def add_documents(self, documents: list[EmbeddingDocument]) -> int:
        """Add documents to the store. Returns count added."""
        ...

    @abstractmethod
    def delete_documents(self, chunk_ids: list[str]) -> int:
        """Delete documents by chunk IDs. Returns count deleted."""
        ...

    @abstractmethod
    def update_documents(self, documents: list[EmbeddingDocument]) -> int:
        """Update existing documents. Returns count updated."""
        ...

    @abstractmethod
    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        """Similarity search. Returns top-K results."""
        ...

    @abstractmethod
    def count(self) -> int:
        """Return total number of stored vectors."""
        ...

    @abstractmethod
    def clear(self) -> None:
        """Remove all stored vectors."""
        ...
