"""
Bulk indexing service for the Knowledge Layer.

Capabilities:
- Index hundreds of documents efficiently
- Batch embedding generation
- Progress reporting via callbacks
- Resume support (skip already-indexed documents)
- Duplicate detection via content hashing
- Incremental indexing
- Aggregated statistics
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Callable

from app.analysis.knowledge.models import KnowledgeDocument
from app.analysis.knowledge.ingestion import IngestionPipeline
from app.analysis.knowledge.storage.postgres_metadata import PostgresMetadataStore
from app.analysis.knowledge.metrics import IngestionMetrics, MetricsCollector

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int, int, str], None]  # (current, total, message)


@dataclass
class BulkIndexResult:
    """Result of a bulk indexing operation."""
    total_submitted: int = 0
    total_processed: int = 0
    total_skipped: int = 0
    total_failed: int = 0
    total_duplicates: int = 0
    total_chunks: int = 0
    total_embeddings: int = 0
    total_time_ms: float = 0.0
    failed_documents: list[str] = field(default_factory=list)  # document_ids that failed
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "total_submitted": self.total_submitted,
            "total_processed": self.total_processed,
            "total_skipped": self.total_skipped,
            "total_failed": self.total_failed,
            "total_duplicates": self.total_duplicates,
            "total_chunks": self.total_chunks,
            "total_embeddings": self.total_embeddings,
            "total_time_ms": round(self.total_time_ms, 2),
            "failed_documents": self.failed_documents,
        }


class BulkIndexer:
    """
    Bulk document indexer with resume, dedup, and progress support.
    
    Uses IngestionPipeline for per-document processing while adding
    bulk orchestration on top.
    """

    def __init__(
        self,
        ingestion_pipeline: IngestionPipeline,
        metadata_store: PostgresMetadataStore,
        metrics_collector: MetricsCollector | None = None,
    ):
        self._pipeline = ingestion_pipeline
        self._metadata_store = metadata_store
        self._metrics = metrics_collector
        self._content_hashes: dict[str, str] = {}  # content_hash -> document_id (for dedup within a batch)

    def index_batch(
        self,
        documents: list[KnowledgeDocument],
        skip_existing: bool = True,
        detect_duplicates: bool = True,
        progress_callback: ProgressCallback | None = None,
    ) -> BulkIndexResult:
        """Index a batch of documents.
        
        Args:
            documents: List of documents to index.
            skip_existing: If True, skip documents whose document_id already exists in metadata store.
            detect_duplicates: If True, skip documents with duplicate content hashes.
            progress_callback: Optional callback called with (current_index, total, status_message).
        """
        result = BulkIndexResult(total_submitted=len(documents))
        start = time.monotonic()
        
        # Build content hash index for current batch dedup
        if detect_duplicates:
            self._content_hashes.clear()
        
        for i, doc in enumerate(documents):
            doc_label = doc.document_id[:12]
            
            try:
                # 1. Check if already indexed (resume support)
                if skip_existing:
                    existing = self._metadata_store.get_document(doc.document_id)
                    if existing:
                        result.total_skipped += 1
                        if progress_callback:
                            progress_callback(i + 1, len(documents), f"Skipped (exists): {doc_label}")
                        continue
                
                # 2. Duplicate detection by content hash
                if detect_duplicates:
                    content_hash = IngestionPipeline.compute_content_hash(doc.content)
                    if content_hash in self._content_hashes:
                        result.total_duplicates += 1
                        result.total_skipped += 1
                        if progress_callback:
                            progress_callback(i + 1, len(documents), f"Skipped (duplicate): {doc_label}")
                        continue
                    self._content_hashes[content_hash] = doc.document_id
                
                # 3. Ingest through pipeline
                metrics = self._pipeline.ingest_document(doc)
                result.total_processed += metrics.documents_processed
                result.total_chunks += metrics.chunks_created
                result.total_embeddings += metrics.embeddings_generated
                result.total_skipped += metrics.documents_skipped
                result.total_duplicates += metrics.duplicates_detected
                
                if progress_callback:
                    progress_callback(i + 1, len(documents), f"Indexed: {doc_label}")
                    
            except Exception as e:
                logger.error("Bulk indexing failed for document '%s': %s", doc.document_id, e)
                result.total_failed += 1
                result.failed_documents.append(doc.document_id)
                if progress_callback:
                    progress_callback(i + 1, len(documents), f"Failed: {doc_label}")
        
        result.total_time_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Bulk indexing complete: %d processed, %d skipped, %d failed out of %d submitted in %.1f ms",
            result.total_processed, result.total_skipped, result.total_failed,
            result.total_submitted, result.total_time_ms,
        )
        return result

    def reindex_document(self, document: KnowledgeDocument) -> IngestionMetrics:
        """Force reindex by removing existing data and re-ingesting."""
        # Remove existing
        self._metadata_store.delete_chunks_by_document(document.document_id)
        self._metadata_store.delete_document(document.document_id)
        # Re-ingest
        return self._pipeline.ingest_document(document)
