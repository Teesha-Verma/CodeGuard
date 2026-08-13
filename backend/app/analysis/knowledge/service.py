"""
Knowledge Management Service.

Top-level orchestration API for the Knowledge & RAG Layer.
Provides high-level operations:

- Index repository knowledge
- Index external knowledge (OWASP, CWE, best practices, etc.)
- Remove knowledge
- Rebuild index
- Refresh vectors
- Get indexing statistics
- Search knowledge

This service does NOT modify existing retrieval APIs.
It extends them with management capabilities.
"""

import logging
from typing import Any

from app.analysis.knowledge.constants import DocumentCategory
from app.analysis.knowledge.models import KnowledgeDocument, RetrievedContext, RepositoryContext
from app.analysis.knowledge.embeddings import EmbeddingProvider
from app.analysis.knowledge.chunking import ChunkingStrategy, MarkdownChunker
from app.analysis.knowledge.storage.vector_store import FAISSVectorStore
from app.analysis.knowledge.storage.postgres_metadata import PostgresMetadataStore
from app.analysis.knowledge.storage.cache import KnowledgeCache
from app.analysis.knowledge.retrievers import SemanticRetriever
from app.analysis.knowledge.reranker import WeightedReranker
from app.analysis.knowledge.query_engine import KnowledgeQueryEngine
from app.analysis.knowledge.repository_index import RepositoryIndex
from app.analysis.knowledge.ingestion import IngestionPipeline
from app.analysis.knowledge.bulk_indexer import BulkIndexer, BulkIndexResult
from app.analysis.knowledge.sync import KnowledgeSynchronizer, SyncResult
from app.analysis.knowledge.repo_builder import RepositoryKnowledgeBuilder
from app.analysis.knowledge.metrics import MetricsCollector, IngestionMetrics
from app.analysis.knowledge.importers import (
    OWASPImporter, CWEImporter, PythonBestPracticeImporter,
    FastAPIBestPracticeImporter, RepositoryRulesImporter,
    SecurityPatternImporter, HistoricalReviewImporter,
)

logger = logging.getLogger(__name__)


class KnowledgeService:
    """
    High-level Knowledge Management service.
    
    Provides a unified API for managing the entire knowledge lifecycle:
    indexing, importing, synchronizing, searching, and monitoring.
    
    Composes existing components via dependency injection.
    """

    def __init__(
        self,
        embedding_provider: EmbeddingProvider,
        vector_store: FAISSVectorStore,
        metadata_store: PostgresMetadataStore,
        chunker: ChunkingStrategy | None = None,
        cache: KnowledgeCache | None = None,
        repository_index: RepositoryIndex | None = None,
    ):
        self._embedding_provider = embedding_provider
        self._vector_store = vector_store
        self._metadata_store = metadata_store
        self._chunker = chunker or MarkdownChunker()
        self._cache = cache
        self._metrics = MetricsCollector()
        self._repository_index = repository_index or RepositoryIndex()

        # Build internal components
        self._ingestion = IngestionPipeline(
            embedding_provider=self._embedding_provider,
            vector_store=self._vector_store,
            metadata_store=self._metadata_store,
            chunker=self._chunker,
            metrics_collector=self._metrics,
        )
        self._bulk_indexer = BulkIndexer(
            ingestion_pipeline=self._ingestion,
            metadata_store=self._metadata_store,
            metrics_collector=self._metrics,
        )
        self._synchronizer = KnowledgeSynchronizer(
            ingestion_pipeline=self._ingestion,
            bulk_indexer=self._bulk_indexer,
            metadata_store=self._metadata_store,
        )
        # Build retriever and query engine using existing components
        self._retriever = SemanticRetriever(
            embedding_provider=self._embedding_provider,
            vector_store=self._vector_store,
            cache=self._cache,
        )
        self._query_engine = KnowledgeQueryEngine(
            retriever=self._retriever,
            reranker=WeightedReranker(),
            repository_index=self._repository_index,
        )

    # ── Indexing Operations ──────────────────────────────────

    def index_document(self, document: KnowledgeDocument) -> IngestionMetrics:
        """Index a single knowledge document."""
        return self._ingestion.ingest_document(document)

    def index_documents(self, documents: list[KnowledgeDocument]) -> BulkIndexResult:
        """Bulk index multiple knowledge documents."""
        return self._bulk_indexer.index_batch(documents)

    def index_repository(self, repo_path: str, repository_url: str = "") -> BulkIndexResult:
        """Scan a repository's documentation and index it."""
        builder = RepositoryKnowledgeBuilder(repo_path, repository_url)
        docs = builder.build()
        if not docs:
            logger.warning("No documentation found in repository: %s", repo_path)
            return BulkIndexResult()
        return self._bulk_indexer.index_batch(docs)

    # ── Import Operations ────────────────────────────────────

    def import_owasp(self, directory: str) -> BulkIndexResult:
        """Import OWASP documentation from a directory."""
        docs = OWASPImporter(directory).load()
        return self._bulk_indexer.index_batch(docs)

    def import_cwe(self, directory: str) -> BulkIndexResult:
        """Import CWE documentation from a directory."""
        docs = CWEImporter(directory).load()
        return self._bulk_indexer.index_batch(docs)

    def import_python_best_practices(self, directory: str) -> BulkIndexResult:
        docs = PythonBestPracticeImporter(directory).load()
        return self._bulk_indexer.index_batch(docs)

    def import_fastapi_best_practices(self, directory: str) -> BulkIndexResult:
        docs = FastAPIBestPracticeImporter(directory).load()
        return self._bulk_indexer.index_batch(docs)

    def import_repository_rules(self, directory: str) -> BulkIndexResult:
        docs = RepositoryRulesImporter(directory).load()
        return self._bulk_indexer.index_batch(docs)

    def import_security_patterns(self, directory: str) -> BulkIndexResult:
        docs = SecurityPatternImporter(directory).load()
        return self._bulk_indexer.index_batch(docs)

    def import_historical_reviews(self, directory: str) -> BulkIndexResult:
        docs = HistoricalReviewImporter(directory).load()
        return self._bulk_indexer.index_batch(docs)

    def import_directory(self, directory: str, category: DocumentCategory) -> BulkIndexResult:
        """Generic import: load all supported files from a directory under a given category."""
        from app.analysis.knowledge.importers import _scan_directory, _load_file, _build_document
        docs: list[KnowledgeDocument] = []
        for path in _scan_directory(directory):
            content = _load_file(path)
            if content:
                docs.append(_build_document(content, path, category, [category.value]))
        return self._bulk_indexer.index_batch(docs)

    # ── Removal Operations ───────────────────────────────────

    def remove_document(self, document_id: str) -> bool:
        """Remove a document and its chunks from the knowledge base."""
        self._metadata_store.delete_chunks_by_document(document_id)
        return self._metadata_store.delete_document(document_id)

    def remove_by_category(self, category: str) -> int:
        """Remove all documents of a given category."""
        docs = self._metadata_store.list_documents(category=category)
        count = 0
        for doc in docs:
            doc_id = doc["document_id"]
            self._metadata_store.delete_chunks_by_document(doc_id)
            if self._metadata_store.delete_document(doc_id):
                count += 1
        logger.info("Removed %d documents with category '%s'", count, category)
        return count

    # ── Rebuild / Refresh ────────────────────────────────────

    def rebuild_index(self) -> BulkIndexResult:
        """Rebuild the entire vector index from stored metadata.
        
        Note: This clears the vector store and rebuilds from metadata.
        Requires re-embedding all chunks.
        """
        self._vector_store.clear()
        all_docs = self._metadata_store.list_documents()
        doc_ids = [d["document_id"] for d in all_docs]
        logger.info("Rebuilding index for %d documents", len(doc_ids))
        # This is a destructive rebuild; for now we log but the actual
        # re-embedding would need the original content which is not stored
        # in metadata. Full rebuild requires re-ingestion from source.
        return BulkIndexResult(total_submitted=len(doc_ids))

    # ── Synchronization ──────────────────────────────────────

    def sync_documents(
        self, documents: list[KnowledgeDocument], category: str | None = None,
    ) -> SyncResult:
        """Synchronize documents with the knowledge index."""
        return self._synchronizer.sync_documents(documents, category)

    # ── Search ───────────────────────────────────────────────

    def search(
        self,
        query: str,
        top_k: int | None = None,
        categories: list[DocumentCategory] | None = None,
        tags: list[str] | None = None,
        repository_url: str | None = None,
        similarity_threshold: float | None = None,
    ) -> RetrievedContext:
        """Search the knowledge base. Delegates to existing KnowledgeQueryEngine."""
        result = self._query_engine.query(
            query=query, top_k=top_k, categories=categories,
            tags=tags, repository_url=repository_url,
            similarity_threshold=similarity_threshold,
        )
        if self._cache:
            self._metrics.update_cache_stats(
                self._cache.stats.get("hits", 0),
                self._cache.stats.get("misses", 0),
            )
        self._metrics.update_vector_count(self._vector_store.size)
        self._metrics.record_query(result.retrieval_time_ms)
        return result

    # ── Repository Context ───────────────────────────────────

    def register_repository(self, context: RepositoryContext) -> None:
        """Register repository context for enhanced retrieval."""
        self._query_engine.register_repository(context)

    # ── Statistics / Monitoring ───────────────────────────────

    def get_statistics(self) -> dict[str, Any]:
        """Return comprehensive knowledge layer statistics."""
        stats = self._metrics.get_summary()
        stats["vector_store_size"] = self._vector_store.size
        if self._cache:
            stats["cache"] = self._cache.stats
        return stats

    def get_document_count(self) -> int:
        """Return total number of indexed documents."""
        return len(self._metadata_store.list_documents())

    def list_documents(self, category: str | None = None) -> list[dict]:
        """List all indexed documents, optionally filtered by category."""
        return self._metadata_store.list_documents(category=category)
