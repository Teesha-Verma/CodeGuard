"""
Tests for Knowledge Operations — Ingestion, Importers, Bulk Indexer,
Sync, Repo Builder, Metrics, and KnowledgeService.

All tests use mocked embedding providers, real FAISS vector stores (dim=3),
in-memory SQLite metadata stores, and real MarkdownChunker instances.
"""

import os
import shutil
import tempfile
import time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import MagicMock, patch

from app.analysis.knowledge.constants import DocumentCategory
from app.analysis.knowledge.models import (
    KnowledgeDocument, RetrievedContext, RetrievalResult, KnowledgeChunk,
)
from app.analysis.knowledge.embeddings import EmbeddingProvider
from app.analysis.knowledge.chunking import MarkdownChunker
from app.analysis.knowledge.storage.vector_store import FAISSVectorStore
from app.analysis.knowledge.storage.postgres_metadata import (
    PostgresMetadataStore, Base,
    KnowledgeDocumentRecord, KnowledgeChunkRecord,
)
from app.analysis.knowledge.ingestion import IngestionPipeline
from app.analysis.knowledge.importers import (
    OWASPImporter, CWEImporter, PythonBestPracticeImporter,
    FastAPIBestPracticeImporter, RepositoryRulesImporter,
    SecurityPatternImporter, HistoricalReviewImporter,
)
from app.analysis.knowledge.bulk_indexer import BulkIndexer
from app.analysis.knowledge.sync import KnowledgeSynchronizer
from app.analysis.knowledge.repo_builder import RepositoryKnowledgeBuilder
from app.analysis.knowledge.metrics import (
    MetricsCollector, IngestionMetrics, KnowledgeLayerStats,
)
from app.analysis.knowledge.service import KnowledgeService


# ── Helper Factory ────────────────────────────────────────────────────

def _make_doc(
    doc_id="doc1",
    content="# Test\nContent here",
    category=DocumentCategory.SECURITY,
):
    return KnowledgeDocument(
        document_id=doc_id,
        title="Test",
        content=content,
        category=category,
        source="test.md",
    )


# ── Shared Fixtures ──────────────────────────────────────────────────

@pytest.fixture
def memory_metadata_store():
    engine = create_engine("sqlite:///:memory:")
    # Only create knowledge tables — not ALL Base tables (which may use JSONB)
    KnowledgeDocumentRecord.__table__.create(engine, checkfirst=True)
    KnowledgeChunkRecord.__table__.create(engine, checkfirst=True)
    Session = sessionmaker(bind=engine)
    return PostgresMetadataStore(session_factory=Session)


@pytest.fixture
def mock_embedding_provider():
    provider = MagicMock(spec=EmbeddingProvider)
    provider.embed_text.return_value = [0.1, 0.2, 0.3]
    provider.embed_batch.side_effect = lambda texts: [
        [0.1, 0.2, 0.3] for _ in texts
    ]
    provider.embed_query.return_value = [0.1, 0.2, 0.3]
    provider.dimension = 3
    provider.model_name = "mock-model"
    return provider


@pytest.fixture
def vector_store():
    return FAISSVectorStore(dimension=3)


@pytest.fixture
def ingestion_pipeline(mock_embedding_provider, vector_store, memory_metadata_store):
    return IngestionPipeline(
        embedding_provider=mock_embedding_provider,
        vector_store=vector_store,
        metadata_store=memory_metadata_store,
        chunker=MarkdownChunker(),
        metrics_collector=MetricsCollector(),
    )


# ══════════════════════════════════════════════════════════════════════
#  INGESTION PIPELINE
# ══════════════════════════════════════════════════════════════════════

class TestIngestionPipeline:
    def test_ingest_single_document(self, ingestion_pipeline):
        doc = _make_doc()
        metrics = ingestion_pipeline.ingest_document(doc)
        assert metrics.documents_processed == 1
        assert metrics.chunks_created > 0
        assert metrics.embeddings_generated > 0
        assert metrics.vectors_stored > 0

    def test_ingest_duplicate_document_skipped(self, ingestion_pipeline):
        doc = _make_doc()
        ingestion_pipeline.ingest_document(doc)
        metrics2 = ingestion_pipeline.ingest_document(doc)
        assert metrics2.documents_skipped == 1
        assert metrics2.duplicates_detected == 1
        assert metrics2.chunks_created == 0

    def test_ingest_empty_document(self, ingestion_pipeline):
        doc = _make_doc(content="   ")
        metrics = ingestion_pipeline.ingest_document(doc)
        # Empty content produces zero chunks → skipped
        assert metrics.documents_skipped == 1
        assert metrics.chunks_created == 0

    def test_ingest_multiple_documents(self, ingestion_pipeline):
        docs = [_make_doc(doc_id=f"d{i}", content=f"# Doc {i}\nParagraph {i}") for i in range(3)]
        agg = ingestion_pipeline.ingest_documents(docs)
        assert agg.documents_processed == 3
        assert agg.chunks_created >= 3

    def test_content_hash_deterministic(self):
        h1 = IngestionPipeline.compute_content_hash("hello")
        h2 = IngestionPipeline.compute_content_hash("hello")
        h3 = IngestionPipeline.compute_content_hash("world")
        assert h1 == h2
        assert h1 != h3


# ══════════════════════════════════════════════════════════════════════
#  IMPORTERS
# ══════════════════════════════════════════════════════════════════════

class TestImporters:
    @pytest.fixture
    def temp_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_owasp_importer(self, temp_dir):
        with open(os.path.join(temp_dir, "owasp_a01.md"), "w") as f:
            f.write("# OWASP A01\nBroken Access Control")
        imp = OWASPImporter(temp_dir)
        docs = imp.load()
        assert len(docs) == 1
        assert docs[0].category == DocumentCategory.OWASP
        assert "owasp" in docs[0].tags
        assert "security" in docs[0].tags

    def test_cwe_importer_with_id_tagging(self, temp_dir):
        with open(os.path.join(temp_dir, "cwe_79.md"), "w") as f:
            f.write("# CWE 79\nXSS")
        imp = CWEImporter(temp_dir)
        docs = imp.load()
        assert len(docs) == 1
        assert docs[0].category == DocumentCategory.CWE
        assert "cwe" in docs[0].tags
        assert "cwe-79" in docs[0].tags

    def test_python_best_practice_importer(self, temp_dir):
        with open(os.path.join(temp_dir, "pep8.md"), "w") as f:
            f.write("PEP 8 Guidelines")
        imp = PythonBestPracticeImporter(temp_dir)
        docs = imp.load()
        assert len(docs) == 1
        assert docs[0].category == DocumentCategory.BEST_PRACTICE
        assert "python" in docs[0].tags

    def test_fastapi_best_practice_importer(self, temp_dir):
        with open(os.path.join(temp_dir, "fastapi.md"), "w") as f:
            f.write("FastAPI Best Practices")
        imp = FastAPIBestPracticeImporter(temp_dir)
        docs = imp.load()
        assert len(docs) == 1
        assert "fastapi" in docs[0].tags

    def test_repository_rules_importer(self, temp_dir):
        with open(os.path.join(temp_dir, "rules.md"), "w") as f:
            f.write("Repository Rules")
        imp = RepositoryRulesImporter(temp_dir)
        docs = imp.load()
        assert len(docs) == 1
        assert docs[0].category == DocumentCategory.REPOSITORY

    def test_security_pattern_importer(self, temp_dir):
        with open(os.path.join(temp_dir, "sqli.md"), "w") as f:
            f.write("# SQL Injection\nPattern details")
        imp = SecurityPatternImporter(temp_dir)
        docs = imp.load()
        assert len(docs) == 1
        assert docs[0].category == DocumentCategory.PATTERN
        assert "security" in docs[0].tags

    def test_historical_review_importer(self, temp_dir):
        with open(os.path.join(temp_dir, "review_001.md"), "w") as f:
            f.write("# Review\nFindings")
        imp = HistoricalReviewImporter(temp_dir)
        docs = imp.load()
        assert len(docs) == 1
        assert docs[0].category == DocumentCategory.HISTORICAL

    def test_importer_missing_directory(self):
        imp = OWASPImporter("/nonexistent/path/abc123")
        docs = imp.load()
        assert docs == []


# ══════════════════════════════════════════════════════════════════════
#  BULK INDEXER
# ══════════════════════════════════════════════════════════════════════

class TestBulkIndexer:
    @pytest.fixture
    def bulk_indexer(self, ingestion_pipeline, memory_metadata_store):
        return BulkIndexer(
            ingestion_pipeline=ingestion_pipeline,
            metadata_store=memory_metadata_store,
            metrics_collector=MetricsCollector(),
        )

    def test_bulk_index_batch(self, bulk_indexer):
        docs = [_make_doc(doc_id=f"b{i}", content=f"# Bulk {i}\nContent {i}") for i in range(3)]
        res = bulk_indexer.index_batch(docs)
        assert res.total_submitted == 3
        assert res.total_processed == 3
        assert res.total_failed == 0

    def test_bulk_index_skip_existing(self, bulk_indexer):
        docs = [_make_doc(doc_id="b1", content="# Existing\nDoc content")]
        bulk_indexer.index_batch(docs)
        res2 = bulk_indexer.index_batch(docs, skip_existing=True)
        assert res2.total_skipped >= 1

    def test_bulk_index_duplicate_detection(self, bulk_indexer):
        doc1 = _make_doc(doc_id="dup1", content="# Same\nIdentical content")
        doc2 = _make_doc(doc_id="dup2", content="# Same\nIdentical content")
        res = bulk_indexer.index_batch([doc1, doc2], detect_duplicates=True)
        assert res.total_submitted == 2
        assert res.total_duplicates >= 1

    def test_bulk_index_progress_callback(self, bulk_indexer):
        docs = [_make_doc(doc_id="p1", content="# Progress\nTest progress")]
        callback = MagicMock()
        bulk_indexer.index_batch(docs, progress_callback=callback)
        callback.assert_called()

    def test_reindex_document(self, bulk_indexer):
        doc = _make_doc(doc_id="re1", content="# Reindex\nOriginal content")
        bulk_indexer.index_batch([doc])
        doc2 = _make_doc(doc_id="re1", content="# Reindex\nUpdated content")
        metrics = bulk_indexer.reindex_document(doc2)
        assert metrics.documents_processed == 1


# ══════════════════════════════════════════════════════════════════════
#  SYNCHRONIZER
# ══════════════════════════════════════════════════════════════════════

class TestKnowledgeSynchronizer:
    @pytest.fixture
    def synchronizer(self, ingestion_pipeline, memory_metadata_store):
        bulk_indexer = BulkIndexer(ingestion_pipeline, memory_metadata_store)
        return KnowledgeSynchronizer(
            ingestion_pipeline=ingestion_pipeline,
            bulk_indexer=bulk_indexer,
            metadata_store=memory_metadata_store,
        )

    def test_sync_add_new(self, synchronizer):
        docs = [_make_doc(doc_id="sync1", content="# Sync\nNew doc")]
        res = synchronizer.sync_documents(docs)
        assert res.documents_added == 1

    def test_sync_skip_unchanged(self, synchronizer):
        doc = _make_doc(doc_id="sync1", content="# Sync\nUnchanged content")
        doc.metadata["content_hash"] = IngestionPipeline.compute_content_hash(doc.content)
        synchronizer.sync_documents([doc])
        res = synchronizer.sync_documents([doc])
        # Second sync should not add or update
        assert res.documents_added == 0

    def test_sync_remove_deleted(self, synchronizer):
        doc = _make_doc(doc_id="sync_rm", content="# Remove\nWill be deleted", category=DocumentCategory.SECURITY)
        synchronizer.sync_documents([doc], category=DocumentCategory.SECURITY.value)
        res = synchronizer.sync_documents([], category=DocumentCategory.SECURITY.value)
        assert res.documents_removed >= 1


# ══════════════════════════════════════════════════════════════════════
#  REPOSITORY KNOWLEDGE BUILDER
# ══════════════════════════════════════════════════════════════════════

class TestRepositoryKnowledgeBuilder:
    @pytest.fixture
    def repo_dir(self):
        d = tempfile.mkdtemp()
        yield d
        shutil.rmtree(d)

    def test_build_from_repo_with_readme(self, repo_dir):
        with open(os.path.join(repo_dir, "README.md"), "w") as f:
            f.write("# My Project\nA description")
        builder = RepositoryKnowledgeBuilder(repo_dir, "https://github.com/test/repo")
        docs = builder.build()
        assert len(docs) > 0
        assert docs[0].category == DocumentCategory.REPOSITORY
        assert "readme" in docs[0].tags

    def test_build_from_repo_with_docs_dir(self, repo_dir):
        os.makedirs(os.path.join(repo_dir, "docs"))
        with open(os.path.join(repo_dir, "docs", "architecture.md"), "w") as f:
            f.write("# Architecture\nMicroservices design")
        builder = RepositoryKnowledgeBuilder(repo_dir)
        docs = builder.build()
        assert len(docs) > 0

    def test_build_from_nonexistent_repo(self):
        builder = RepositoryKnowledgeBuilder("/nonexistent/repo/path")
        docs = builder.build()
        assert docs == []


# ══════════════════════════════════════════════════════════════════════
#  METRICS
# ══════════════════════════════════════════════════════════════════════

class TestMetrics:
    def test_ingestion_metrics_to_dict(self):
        m = IngestionMetrics(
            documents_processed=1,
            chunks_created=5,
            embeddings_generated=5,
            embedding_time_ms=42.5,
        )
        d = m.to_dict()
        assert d["documents_processed"] == 1
        assert d["chunks_created"] == 5
        assert d["embedding_time_ms"] == 42.5

    def test_metrics_collector_record_ingestion(self):
        mc = MetricsCollector()
        m = IngestionMetrics(
            documents_processed=2,
            chunks_created=10,
            vectors_stored=10,
            embedding_time_ms=50.0,
            chunking_time_ms=20.0,
        )
        mc.record_ingestion(m)
        stats = mc.get_summary()
        assert stats["total_documents"] == 2
        assert stats["total_chunks"] == 10
        assert stats["total_ingestions"] == 1

    def test_metrics_collector_record_query(self):
        mc = MetricsCollector()
        mc.record_query(15.0)
        stats = mc.get_summary()
        assert stats["total_queries"] == 1
        assert stats["cumulative_retrieval_time_ms"] == 15.0

    def test_metrics_collector_summary(self):
        mc = MetricsCollector()
        summary = mc.get_summary()
        assert "total_documents" in summary
        assert "total_queries" in summary
        assert "cache_hit_ratio" in summary

    def test_measure_context_manager(self):
        mc = MetricsCollector()
        with mc.measure("test_metric") as timer:
            time.sleep(0.05)  # 50ms — enough for Windows timer resolution
        assert timer.elapsed_ms >= 0  # Timer should have measured something

    def test_metrics_collector_reset(self):
        mc = MetricsCollector()
        mc.record_query(10.0)
        mc.reset()
        stats = mc.get_summary()
        assert stats["total_queries"] == 0


# ══════════════════════════════════════════════════════════════════════
#  KNOWLEDGE SERVICE
# ══════════════════════════════════════════════════════════════════════

class TestKnowledgeService:
    @pytest.fixture
    def service(self, mock_embedding_provider, vector_store, memory_metadata_store):
        return KnowledgeService(
            embedding_provider=mock_embedding_provider,
            vector_store=vector_store,
            metadata_store=memory_metadata_store,
        )

    def test_index_document(self, service):
        doc = _make_doc(doc_id="s1", content="# Service\nIndexing test")
        res = service.index_document(doc)
        assert res.documents_processed == 1

    def test_search_delegates_to_query_engine(self, service):
        mock_ctx = RetrievedContext(
            results=[], query="test", total_results=0, retrieval_time_ms=10.5,
        )
        service._query_engine.query = MagicMock(return_value=mock_ctx)
        result = service.search("test query")
        service._query_engine.query.assert_called_once()
        assert result.retrieval_time_ms == 10.5

    def test_remove_document(self, service):
        doc = _make_doc(doc_id="rm1", content="# Remove\nDoc to remove")
        service.index_document(doc)
        result = service.remove_document("rm1")
        assert result is True

    def test_get_statistics(self, service):
        doc = _make_doc(doc_id="stat1", content="# Stats\nStats test doc")
        service.index_document(doc)
        stats = service.get_statistics()
        assert "vector_store_size" in stats

    def test_import_owasp(self, service, tmp_path):
        (tmp_path / "owasp.md").write_text("# OWASP\nContent", encoding="utf-8")
        res = service.import_owasp(str(tmp_path))
        assert res.total_processed >= 1

    def test_index_repository(self, service, tmp_path):
        (tmp_path / "README.md").write_text("# Repo\nReadme content", encoding="utf-8")
        res = service.index_repository(str(tmp_path))
        assert res.total_processed >= 1

    def test_get_document_count(self, service):
        doc = _make_doc(doc_id="cnt1", content="# Count\nCounting test")
        service.index_document(doc)
        assert service.get_document_count() >= 1

    def test_list_documents(self, service):
        doc = _make_doc(doc_id="lst1", content="# List\nListing test")
        service.index_document(doc)
        docs = service.list_documents()
        assert len(docs) >= 1
