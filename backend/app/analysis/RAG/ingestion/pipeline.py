"""RAG indexing pipeline.

Orchestrates the complete flow:
  Discover → Parse → Validate → Chunk → Embed → Store

Supports incremental indexing via content hash comparison.
"""
from __future__ import annotations

import time
from typing import Any

from app.analysis.RAG.config.settings import RAGConfig
from app.analysis.RAG.embeddings.base import EmbeddingProvider
from app.analysis.RAG.ingestion.chunker import chunk_documents
from app.analysis.RAG.ingestion.discovery import discover_knowledge_files
from app.analysis.RAG.ingestion.parser import parse_document
from app.analysis.RAG.ingestion.validator import validate_batch
from app.analysis.RAG.models.documents import (
    EmbeddingDocument, KnowledgeChunk, KnowledgeDocument,
)
from app.analysis.RAG.utils.logging import PipelineStats, get_logger, timed_operation
from app.analysis.RAG.vector_store.base import VectorStore

logger = get_logger("pipeline")


class IndexingPipeline:
    """Orchestrates knowledge indexing: discovery → parse → validate → chunk → embed → store."""

    def __init__(
        self,
        config: RAGConfig,
        embedding_provider: EmbeddingProvider,
        vector_store: VectorStore,
    ):
        self._config = config
        self._embedder = embedding_provider
        self._store = vector_store
        self._indexed_hashes: dict[str, str] = {}  # source_path -> content_hash

    def run(
        self,
        force_reindex: bool = False,
    ) -> PipelineStats:
        """Execute the full indexing pipeline."""
        stats = PipelineStats()
        start = time.monotonic()

        with timed_operation(logger, "full indexing pipeline"):
            # 1. Discover
            file_paths = discover_knowledge_files(
                self._config.knowledge_dir,
                self._config.supported_extensions,
            )
            stats.files_discovered = len(file_paths)

            # 2. Parse
            documents: list[KnowledgeDocument] = []
            for path in file_paths:
                doc = parse_document(path)
                if doc is None:
                    stats.files_failed += 1
                    stats.errors.append(f"Parse failed: {path}")
                    continue

                # Incremental check
                if not force_reindex:
                    old_hash = self._indexed_hashes.get(path)
                    if old_hash and old_hash == doc.content_hash:
                        stats.files_skipped += 1
                        continue

                documents.append(doc)
                stats.files_parsed += 1

            if not documents:
                logger.info("No new or changed documents to index.")
                stats.total_time_ms = (time.monotonic() - start) * 1000
                return stats

            # 3. Validate
            validation_results = validate_batch(documents)
            valid_docs: list[KnowledgeDocument] = []
            for doc, vr in zip(documents, validation_results):
                stats.validation_warnings += len(
                    [i for i in vr.issues if i.severity == "warning"]
                )
                if vr.is_valid:
                    valid_docs.append(doc)
                else:
                    stats.validation_errors += len(
                        [i for i in vr.issues if i.severity == "error"]
                    )
                    stats.files_failed += 1
                    stats.errors.append(f"Validation failed: {doc.source_path}")

            # 4. Chunk
            all_chunks = chunk_documents(valid_docs, self._config.chunking)
            stats.chunks_created = len(all_chunks)

            # 5. Embed
            if all_chunks:
                texts = [c.content for c in all_chunks]
                embeddings = self._embedder.embed_batch(texts)
                stats.embeddings_generated = len(embeddings)

                # 6. Store
                embedding_docs = []
                for chunk, emb in zip(all_chunks, embeddings):
                    meta = chunk.metadata
                    embedding_docs.append(
                        EmbeddingDocument(
                            chunk_id=chunk.chunk_id,
                            document_id=chunk.document_id,
                            content=chunk.content,
                            embedding=emb,
                            metadata={
                                "category": meta.category if meta else "",
                                "subcategory": meta.subcategory if meta else "",
                                "severity": meta.severity.value if meta else "",
                                "tags": meta.tags if meta else [],
                                "section_title": chunk.section_title,
                                "source_path": chunk.source_path,
                            },
                        )
                    )
                self._store.add_documents(embedding_docs)
                stats.vectors_stored = len(embedding_docs)

            # Update hash cache
            for doc in valid_docs:
                self._indexed_hashes[doc.source_path] = doc.content_hash

        stats.total_time_ms = (time.monotonic() - start) * 1000
        logger.info(
            "Pipeline complete: %d parsed, %d chunks, %d vectors in %.1f ms",
            stats.files_parsed, stats.chunks_created, stats.vectors_stored,
            stats.total_time_ms,
        )
        return stats
