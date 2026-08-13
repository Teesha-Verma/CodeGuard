"""
Knowledge Layer metrics and monitoring.

Collects operational metrics for:
- Document and chunk counts
- Embedding generation timing
- Chunking timing
- Retrieval latency
- Cache statistics
- Vector store statistics
- Storage usage
"""

import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class IngestionMetrics:
    """Metrics collected during a single ingestion operation."""
    documents_processed: int = 0
    documents_skipped: int = 0
    documents_failed: int = 0
    chunks_created: int = 0
    embeddings_generated: int = 0
    vectors_stored: int = 0
    metadata_records_saved: int = 0
    duplicates_detected: int = 0
    chunking_time_ms: float = 0.0
    embedding_time_ms: float = 0.0
    storage_time_ms: float = 0.0
    total_time_ms: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        """Serialize metrics to dictionary."""
        return {
            "documents_processed": self.documents_processed,
            "documents_skipped": self.documents_skipped,
            "documents_failed": self.documents_failed,
            "chunks_created": self.chunks_created,
            "embeddings_generated": self.embeddings_generated,
            "vectors_stored": self.vectors_stored,
            "metadata_records_saved": self.metadata_records_saved,
            "duplicates_detected": self.duplicates_detected,
            "chunking_time_ms": round(self.chunking_time_ms, 2),
            "embedding_time_ms": round(self.embedding_time_ms, 2),
            "storage_time_ms": round(self.storage_time_ms, 2),
            "total_time_ms": round(self.total_time_ms, 2),
        }


@dataclass
class KnowledgeLayerStats:
    """Aggregate statistics for the entire Knowledge Layer."""
    total_documents: int = 0
    total_chunks: int = 0
    total_vectors: int = 0
    total_ingestions: int = 0
    total_queries: int = 0
    cumulative_embedding_time_ms: float = 0.0
    cumulative_chunking_time_ms: float = 0.0
    cumulative_retrieval_time_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_ingestion_at: str | None = None
    last_query_at: str | None = None
    categories: dict[str, int] = field(default_factory=dict)  # category -> doc count

    def to_dict(self) -> dict[str, Any]:
        total_cache = self.cache_hits + self.cache_misses
        return {
            "total_documents": self.total_documents,
            "total_chunks": self.total_chunks,
            "total_vectors": self.total_vectors,
            "total_ingestions": self.total_ingestions,
            "total_queries": self.total_queries,
            "cumulative_embedding_time_ms": round(self.cumulative_embedding_time_ms, 2),
            "cumulative_chunking_time_ms": round(self.cumulative_chunking_time_ms, 2),
            "cumulative_retrieval_time_ms": round(self.cumulative_retrieval_time_ms, 2),
            "cache_hit_ratio": round(self.cache_hits / total_cache, 4) if total_cache > 0 else 0.0,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "last_ingestion_at": self.last_ingestion_at,
            "last_query_at": self.last_query_at,
            "categories": dict(self.categories),
        }


class MetricsCollector:
    """Singleton-style metrics collector for the Knowledge Layer."""

    def __init__(self) -> None:
        self._stats = KnowledgeLayerStats()

    @property
    def stats(self) -> KnowledgeLayerStats:
        return self._stats

    @contextmanager
    def measure(self, metric_name: str):
        """Context manager that measures elapsed time in ms and returns it.
        
        Usage:
            with collector.measure('embedding') as timer:
                do_work()
            elapsed = timer.elapsed_ms
        """
        timer = _Timer()
        try:
            yield timer
        finally:
            timer.stop()
            logger.debug("Metric '%s' took %.2f ms", metric_name, timer.elapsed_ms)

    def record_ingestion(self, metrics: IngestionMetrics) -> None:
        """Record completed ingestion metrics."""
        from datetime import datetime, timezone
        self._stats.total_documents += metrics.documents_processed
        self._stats.total_chunks += metrics.chunks_created
        self._stats.total_vectors += metrics.vectors_stored
        self._stats.total_ingestions += 1
        self._stats.cumulative_embedding_time_ms += metrics.embedding_time_ms
        self._stats.cumulative_chunking_time_ms += metrics.chunking_time_ms
        self._stats.last_ingestion_at = datetime.now(timezone.utc).isoformat()

    def record_query(self, retrieval_time_ms: float) -> None:
        """Record a query execution."""
        from datetime import datetime, timezone
        self._stats.total_queries += 1
        self._stats.cumulative_retrieval_time_ms += retrieval_time_ms
        self._stats.last_query_at = datetime.now(timezone.utc).isoformat()

    def update_cache_stats(self, hits: int, misses: int) -> None:
        self._stats.cache_hits = hits
        self._stats.cache_misses = misses

    def update_vector_count(self, count: int) -> None:
        self._stats.total_vectors = count

    def update_category_count(self, category: str, count: int) -> None:
        self._stats.categories[category] = count

    def reset(self) -> None:
        self._stats = KnowledgeLayerStats()

    def get_summary(self) -> dict[str, Any]:
        return self._stats.to_dict()


class _Timer:
    """Internal timer used by MetricsCollector.measure()."""
    def __init__(self):
        self._start = time.monotonic()
        self._elapsed_ms: float = 0.0

    def stop(self):
        self._elapsed_ms = (time.monotonic() - self._start) * 1000

    @property
    def elapsed_ms(self) -> float:
        return self._elapsed_ms
