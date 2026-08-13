"""
Knowledge Base Ingestion Pipeline.

Orchestrates the complete document ingestion flow:
  Load document → Assign category → Create KnowledgeDocument
  → Chunk → Generate embeddings → Store vectors → Store metadata
  → Return ingestion statistics.

Reuses all existing Knowledge Layer components.
"""

import hashlib
import logging
import time
from typing import Any

from app.analysis.knowledge.constants import DocumentCategory, MAX_EMBEDDING_BATCH_SIZE
from app.analysis.knowledge.models import KnowledgeDocument, KnowledgeChunk
from app.analysis.knowledge.chunking import MarkdownChunker, ChunkingStrategy
from app.analysis.knowledge.embeddings import EmbeddingProvider
from app.analysis.knowledge.storage.vector_store import FAISSVectorStore
from app.analysis.knowledge.storage.postgres_metadata import PostgresMetadataStore
from app.analysis.knowledge.metrics import IngestionMetrics, MetricsCollector

logger = logging.getLogger(__name__)


class IngestionPipeline:
    """
    Orchestrates end-to-end knowledge document ingestion.

    Accepts KnowledgeDocument objects and pushes them through:
    chunking → embedding → vector storage → metadata storage.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: FAISSVectorStore,
        metadata_store: PostgresMetadataStore,
        chunker: ChunkingStrategy | None = None,
        metrics_collector: MetricsCollector | None = None,
        batch_size: int = MAX_EMBEDDING_BATCH_SIZE,
    ):
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._metadata_store = metadata_store
        self._chunker = chunker or MarkdownChunker()
        self._metrics = metrics_collector
        self._batch_size = batch_size

    def ingest_document(self, document: KnowledgeDocument) -> IngestionMetrics:
        """Ingest a single KnowledgeDocument through the full pipeline."""
        metrics = IngestionMetrics()
        start = time.monotonic()

        try:
            # 1. Check duplicate
            existing = self._metadata_store.get_document(document.document_id)
            if existing:
                logger.info("Document '%s' already exists, skipping.", document.document_id)
                metrics.documents_skipped = 1
                metrics.duplicates_detected = 1
                return metrics

            # 2. Chunk
            chunk_start = time.monotonic()
            chunks = self._chunker.chunk(document)
            metrics.chunking_time_ms = (time.monotonic() - chunk_start) * 1000
            metrics.chunks_created = len(chunks)

            if not chunks:
                logger.warning("Document '%s' produced zero chunks.", document.document_id)
                metrics.documents_skipped = 1
                return metrics

            # 3. Generate embeddings in batches
            embed_start = time.monotonic()
            all_embeddings: list[list[float]] = []
            texts = [c.content for c in chunks]
            for i in range(0, len(texts), self._batch_size):
                batch = texts[i : i + self._batch_size]
                batch_embeddings = self._embedding_provider.embed_batch(batch)
                all_embeddings.extend(batch_embeddings)
            metrics.embedding_time_ms = (time.monotonic() - embed_start) * 1000
            metrics.embeddings_generated = len(all_embeddings)

            # 4. Store vectors
            storage_start = time.monotonic()
            chunk_ids = [c.chunk_id for c in chunks]
            added = self._vector_store.add_embeddings(chunk_ids, all_embeddings)
            metrics.vectors_stored = added

            # 5. Store document metadata
            self._metadata_store.save_document(
                doc_id=document.document_id,
                title=document.title,
                category=document.category.value if isinstance(document.category, DocumentCategory) else str(document.category),
                source=document.source,
                tags=list(document.tags),
                version=document.version,
                language=document.language,
                chunk_count=len(chunks),
                metadata=dict(document.metadata),
            )
            metrics.metadata_records_saved += 1

            # 6. Store chunk metadata
            for chunk in chunks:
                self._metadata_store.save_chunk_metadata(
                    chunk_id=chunk.chunk_id,
                    document_id=chunk.document_id,
                    chunk_index=chunk.chunk_index,
                    category=chunk.category.value if isinstance(chunk.category, DocumentCategory) else str(chunk.category),
                    tags=list(chunk.tags),
                    content_preview=chunk.content[:200],
                    token_count=chunk.token_count,
                    metadata=dict(chunk.metadata),
                )
                metrics.metadata_records_saved += 1
            metrics.storage_time_ms = (time.monotonic() - storage_start) * 1000

            metrics.documents_processed = 1
            logger.info(
                "Ingested document '%s': %d chunks, %d embeddings in %.1f ms",
                document.document_id, len(chunks), len(all_embeddings),
                (time.monotonic() - start) * 1000,
            )

        except Exception as e:
            logger.error("Failed to ingest document '%s': %s", document.document_id, e)
            metrics.documents_failed = 1
            raise
        finally:
            metrics.total_time_ms = (time.monotonic() - start) * 1000
            if self._metrics:
                self._metrics.record_ingestion(metrics)

        return metrics

    def ingest_documents(self, documents: list[KnowledgeDocument]) -> IngestionMetrics:
        """Ingest multiple documents, aggregating metrics."""
        aggregate = IngestionMetrics()
        start = time.monotonic()

        for doc in documents:
            try:
                m = self.ingest_document(doc)
                aggregate.documents_processed += m.documents_processed
                aggregate.documents_skipped += m.documents_skipped
                aggregate.documents_failed += m.documents_failed
                aggregate.chunks_created += m.chunks_created
                aggregate.embeddings_generated += m.embeddings_generated
                aggregate.vectors_stored += m.vectors_stored
                aggregate.metadata_records_saved += m.metadata_records_saved
                aggregate.duplicates_detected += m.duplicates_detected
                aggregate.chunking_time_ms += m.chunking_time_ms
                aggregate.embedding_time_ms += m.embedding_time_ms
                aggregate.storage_time_ms += m.storage_time_ms
            except Exception:
                aggregate.documents_failed += 1

        aggregate.total_time_ms = (time.monotonic() - start) * 1000
        return aggregate

    @staticmethod
    def compute_content_hash(content: str) -> str:
        """Compute SHA-256 hash of document content for dedup."""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()
