"""
Knowledge synchronization utilities.

Features:
- Detect modified documents (via content hash comparison)
- Skip unchanged files
- Re-index changed files
- Remove deleted documents
- Maintain metadata consistency
"""

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any

from app.analysis.knowledge.models import KnowledgeDocument
from app.analysis.knowledge.ingestion import IngestionPipeline
from app.analysis.knowledge.bulk_indexer import BulkIndexer
from app.analysis.knowledge.storage.postgres_metadata import PostgresMetadataStore

logger = logging.getLogger(__name__)


@dataclass
class SyncResult:
    """Result of a synchronization operation."""
    documents_added: int = 0
    documents_updated: int = 0
    documents_removed: int = 0
    documents_unchanged: int = 0
    total_time_ms: float = 0.0
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "documents_added": self.documents_added,
            "documents_updated": self.documents_updated,
            "documents_removed": self.documents_removed,
            "documents_unchanged": self.documents_unchanged,
            "total_time_ms": round(self.total_time_ms, 2),
            "errors": self.errors,
        }


class KnowledgeSynchronizer:
    """
    Synchronizes knowledge documents between a source and the index.
    
    Detects additions, modifications, and deletions.
    """

    def __init__(
        self,
        ingestion_pipeline: IngestionPipeline,
        bulk_indexer: BulkIndexer,
        metadata_store: PostgresMetadataStore,
    ):
        self._pipeline = ingestion_pipeline
        self._bulk_indexer = bulk_indexer
        self._metadata_store = metadata_store

    def sync_documents(
        self,
        current_documents: list[KnowledgeDocument],
        category: str | None = None,
    ) -> SyncResult:
        """
        Synchronize the provided documents against what's currently indexed.
        
        1. Index new documents
        2. Re-index modified documents (content hash changed)
        3. Remove documents no longer in the source
        """
        result = SyncResult()
        start = time.monotonic()

        # Build map of incoming docs
        incoming_by_id: dict[str, KnowledgeDocument] = {
            doc.document_id: doc for doc in current_documents
        }

        # Get all currently indexed documents
        indexed_docs = self._metadata_store.list_documents(category=category)
        indexed_by_id: dict[str, dict] = {
            d["document_id"]: d for d in indexed_docs
        }

        # Process each incoming document
        for doc_id, doc in incoming_by_id.items():
            try:
                existing = indexed_by_id.get(doc_id)
                if existing is None:
                    # NEW document
                    self._pipeline.ingest_document(doc)
                    result.documents_added += 1
                else:
                    # Check if content changed (compare content hash stored in metadata)
                    new_hash = IngestionPipeline.compute_content_hash(doc.content)
                    old_hash = (existing.get("metadata") or {}).get("content_hash", "")
                    if new_hash != old_hash:
                        # MODIFIED — reindex
                        # Store content_hash in doc metadata for future comparisons
                        doc.metadata["content_hash"] = new_hash
                        self._bulk_indexer.reindex_document(doc)
                        result.documents_updated += 1
                    else:
                        result.documents_unchanged += 1
            except Exception as e:
                logger.error("Sync error for document '%s': %s", doc_id, e)
                result.errors.append(f"{doc_id}: {str(e)}")

        # Remove documents no longer in source
        for doc_id in indexed_by_id:
            if doc_id not in incoming_by_id:
                try:
                    self._metadata_store.delete_chunks_by_document(doc_id)
                    self._metadata_store.delete_document(doc_id)
                    result.documents_removed += 1
                except Exception as e:
                    logger.error("Failed to remove document '%s': %s", doc_id, e)
                    result.errors.append(f"remove {doc_id}: {str(e)}")

        result.total_time_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Sync complete: +%d ~%d -%d =%d in %.1f ms",
            result.documents_added, result.documents_updated,
            result.documents_removed, result.documents_unchanged,
            result.total_time_ms,
        )
        return result
