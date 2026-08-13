"""In-memory vector store implementation.

Simple in-memory storage with brute-force cosine similarity.
Suitable for testing and small knowledge bases.
"""
from __future__ import annotations

import math
from typing import Any

from app.analysis.RAG.models.documents import EmbeddingDocument, SearchResult
from app.analysis.RAG.utils.logging import get_logger
from app.analysis.RAG.vector_store.base import VectorStore

logger = get_logger("vector_store.memory")


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _matches_filters(metadata: dict[str, Any], filters: dict[str, Any]) -> bool:
    """Check if document metadata matches all filter criteria."""
    for key, value in filters.items():
        doc_value = metadata.get(key)
        if isinstance(value, list):
            # Filter value is a list: doc_value must contain at least one item
            if not isinstance(doc_value, list):
                return False
            if not any(v in doc_value for v in value):
                return False
        else:
            if doc_value != value:
                return False
    return True


class InMemoryVectorStore(VectorStore):
    """In-memory vector store with brute-force cosine similarity search."""

    def __init__(self) -> None:
        self._documents: dict[str, EmbeddingDocument] = {}  # chunk_id -> doc

    def add_documents(self, documents: list[EmbeddingDocument]) -> int:
        added = 0
        for doc in documents:
            if doc.chunk_id not in self._documents:
                self._documents[doc.chunk_id] = doc
                added += 1
        logger.debug("Added %d documents (total: %d)", added, len(self._documents))
        return added

    def delete_documents(self, chunk_ids: list[str]) -> int:
        deleted = 0
        for cid in chunk_ids:
            if cid in self._documents:
                del self._documents[cid]
                deleted += 1
        return deleted

    def update_documents(self, documents: list[EmbeddingDocument]) -> int:
        updated = 0
        for doc in documents:
            if doc.chunk_id in self._documents:
                self._documents[doc.chunk_id] = doc
                updated += 1
            else:
                self._documents[doc.chunk_id] = doc
                updated += 1
        return updated

    def search(
        self,
        query_embedding: list[float],
        top_k: int = 10,
        filters: dict[str, Any] | None = None,
    ) -> list[SearchResult]:
        candidates: list[tuple[float, EmbeddingDocument]] = []

        for doc in self._documents.values():
            if not doc.embedding:
                continue
            if filters and not _matches_filters(doc.metadata, filters):
                continue
            score = _cosine_similarity(query_embedding, doc.embedding)
            candidates.append((score, doc))

        candidates.sort(key=lambda x: x[0], reverse=True)
        results: list[SearchResult] = []
        for score, doc in candidates[:top_k]:
            results.append(
                SearchResult(
                    chunk_id=doc.chunk_id,
                    document_id=doc.document_id,
                    content=doc.content,
                    score=score,
                    metadata=doc.metadata,
                    source_path=doc.metadata.get("source_path", ""),
                    section_title=doc.metadata.get("section_title", ""),
                )
            )
        return results

    def count(self) -> int:
        return len(self._documents)

    def clear(self) -> None:
        self._documents.clear()
