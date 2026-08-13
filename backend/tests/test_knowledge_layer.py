"""
Comprehensive tests for the Knowledge & RAG Layer.

Tests cover: models, chunking, cache, providers, repository index,
retriever, reranker, query engine, and postgres metadata storage.
"""
import os
import pytest
import time
import sys
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from pydantic import ValidationError

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.analysis.knowledge.constants import DocumentCategory
from app.analysis.knowledge.models import (
    KnowledgeDocument,
    KnowledgeChunk,
    EmbeddingResult,
    RepositoryContext,
    RetrievalRequest,
    RetrievalResult,
    RetrievedContext,
    MetadataRecord,
)
from app.analysis.knowledge.chunking import MarkdownChunker, CodeChunker
from app.analysis.knowledge.embeddings import EmbeddingProvider
from app.analysis.knowledge.storage.cache import KnowledgeCache
from app.analysis.knowledge.repository_index import RepositoryIndex
from app.analysis.knowledge.reranker import WeightedReranker, RerankerStrategy
from app.analysis.knowledge.retrievers import SemanticRetriever
from app.analysis.knowledge.query_engine import KnowledgeQueryEngine
from app.analysis.knowledge.providers.repository_provider import RepositoryProvider
from app.analysis.knowledge.providers.security_provider import SecurityProvider


# ── Helper Factories ──────────────────────────────────────

def _make_chunk(
    chunk_id: str = "c1",
    document_id: str = "doc1",
    content: str = "Test content",
    chunk_index: int = 0,
    category: DocumentCategory = DocumentCategory.SECURITY,
    tags: list[str] | None = None,
) -> KnowledgeChunk:
    return KnowledgeChunk(
        chunk_id=chunk_id,
        document_id=document_id,
        content=content,
        chunk_index=chunk_index,
        start_offset=0,
        end_offset=len(content),
        category=category,
        tags=tags or [],
        metadata={},
        token_count=len(content.split()),
    )


def _make_document(
    document_id: str = "doc_1",
    title: str = "Test Doc",
    content: str = "Hello world",
    category: DocumentCategory = DocumentCategory.SECURITY,
) -> KnowledgeDocument:
    return KnowledgeDocument(
        document_id=document_id,
        title=title,
        content=content,
        category=category,
        source="manual",
        tags=["test"],
    )


# ---------------------------------------------------------
# 1. Models Tests
# ---------------------------------------------------------
class TestModels:
    def test_knowledge_document_valid(self):
        doc = _make_document()
        assert doc.document_id == "doc_1"
        assert doc.category == DocumentCategory.SECURITY
        assert doc.version == "1.0.0"
        assert doc.language == "en"

    def test_knowledge_document_defaults(self):
        """Document should auto-generate UUID and timestamps if not provided."""
        doc = KnowledgeDocument(
            title="Auto", content="Content",
            category=DocumentCategory.PATTERN, source="test",
        )
        assert len(doc.document_id) > 0
        assert doc.created_at is not None
        assert doc.updated_at is not None

    def test_knowledge_chunk_valid(self):
        chunk = _make_chunk()
        assert chunk.chunk_id == "c1"
        assert chunk.document_id == "doc1"
        assert chunk.category == DocumentCategory.SECURITY

    def test_embedding_result_validation(self):
        emb = EmbeddingResult(chunk_id="c1", embedding=[0.1, 0.2, 0.3], model="test", dimension=3)
        assert emb.dimension == 3

        with pytest.raises(ValidationError):
            EmbeddingResult(chunk_id="c1", embedding=[0.1, 0.2], model="test", dimension=3)

    def test_repository_context_valid(self):
        ctx = RepositoryContext(
            repository_url="https://github.com/test/repo",
            primary_language="python",
            framework="fastapi",
            dependencies=["pydantic"],
        )
        assert ctx.primary_language == "python"
        assert ctx.cfg_summary == {}
        assert ctx.call_graph_summary == {}
        assert ctx.data_flow_summary == {}

    def test_retrieval_request_validation(self):
        req = RetrievalRequest(
            query="test", top_k=5,
            categories=[DocumentCategory.SECURITY],
            similarity_threshold=0.8,
        )
        assert req.top_k == 5

        # Invalid top_k (>50)
        with pytest.raises(ValidationError):
            RetrievalRequest(query="test", top_k=100)

        # Invalid similarity_threshold
        with pytest.raises(ValidationError):
            RetrievalRequest(query="test", similarity_threshold=1.5)

    def test_retrieval_result_valid(self):
        chunk = _make_chunk()
        result = RetrievalResult(
            chunk=chunk, similarity_score=0.9, final_score=0.85,
        )
        assert result.similarity_score == 0.9
        assert result.rerank_score is None

    def test_retrieved_context_valid(self):
        chunk = _make_chunk()
        result = RetrievalResult(chunk=chunk, similarity_score=0.9, final_score=0.9)
        ctx = RetrievedContext(
            results=[result], query="test", total_results=1,
        )
        assert ctx.total_results == 1
        assert ctx.retrieval_time_ms == 0.0

    def test_metadata_record_valid(self):
        rec = MetadataRecord(
            record_id="r1", document_id="doc1",
            category=DocumentCategory.BEST_PRACTICE,
        )
        assert rec.version == "1.0.0"
        assert rec.chunk_id is None


# ---------------------------------------------------------
# 2. Chunking Tests
# ---------------------------------------------------------
class TestChunking:
    def test_markdown_chunker_validation(self):
        chunker = MarkdownChunker(chunk_size=1000, overlap=100)
        assert chunker.chunk_size == 1000

        # Invalid size (too small)
        with pytest.raises(ValueError):
            MarkdownChunker(chunk_size=10)

        # Invalid overlap (>= chunk_size)
        with pytest.raises(ValueError):
            MarkdownChunker(chunk_size=1000, overlap=2000)

    def test_markdown_chunker_split(self):
        doc = _make_document(
            content="# Header 1\nContent under header 1.\n# Header 2\nMore content here.",
        )
        chunker = MarkdownChunker(chunk_size=100, overlap=10)
        chunks = chunker.chunk(doc)

        assert len(chunks) > 0
        assert all(isinstance(c, KnowledgeChunk) for c in chunks)
        assert all(c.document_id == "doc_1" for c in chunks)
        assert all(c.category == DocumentCategory.SECURITY for c in chunks)

    def test_deterministic_chunk_ids(self):
        doc = _make_document(content="# Title\nSome content here")
        chunker = MarkdownChunker(chunk_size=500, overlap=0)
        chunks_1 = chunker.chunk(doc)
        chunks_2 = chunker.chunk(doc)

        assert len(chunks_1) == len(chunks_2)
        for c1, c2 in zip(chunks_1, chunks_2):
            assert c1.chunk_id == c2.chunk_id

    def test_large_section_splitting(self):
        """Sections larger than chunk_size should be split with overlap."""
        large_content = "# Big Section\n" + "word " * 200
        doc = _make_document(content=large_content)
        chunker = MarkdownChunker(chunk_size=100, overlap=20)
        chunks = chunker.chunk(doc)

        assert len(chunks) > 1
        for chunk in chunks:
            assert chunk.token_count > 0

    def test_code_chunker(self):
        doc = _make_document(content="# Code\nSome code content")
        chunker = CodeChunker(chunk_size=500, overlap=50)
        chunks = chunker.chunk(doc)
        assert len(chunks) > 0

    def test_empty_document(self):
        doc = _make_document(content="")
        chunker = MarkdownChunker(chunk_size=500, overlap=0)
        chunks = chunker.chunk(doc)
        assert len(chunks) == 0


# ---------------------------------------------------------
# 3. Cache Tests
# ---------------------------------------------------------
class TestCache:
    def test_cache_put_get(self):
        cache = KnowledgeCache(max_size=10, ttl_seconds=60, enabled=True)
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"
        assert cache.get("key2") is None

        stats = cache.stats
        assert stats["hits"] == 1
        assert stats["misses"] == 1

    def test_cache_ttl_expiry(self):
        cache = KnowledgeCache(max_size=10, ttl_seconds=0, enabled=True)
        cache.put("key1", "value1")
        time.sleep(0.05)
        assert cache.get("key1") is None

    def test_cache_disabled(self):
        cache = KnowledgeCache(max_size=10, ttl_seconds=60, enabled=False)
        cache.put("key1", "value1")
        assert cache.get("key1") is None

    def test_cache_lru_eviction(self):
        cache = KnowledgeCache(max_size=2, ttl_seconds=60, enabled=True)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.put("k3", "v3")  # Evicts k1

        assert cache.get("k1") is None
        assert cache.get("k2") == "v2"
        assert cache.get("k3") == "v3"

    def test_cache_invalidate(self):
        cache = KnowledgeCache(max_size=10, ttl_seconds=60, enabled=True)
        cache.put("k1", "v1")
        assert cache.invalidate("k1") is True
        assert cache.get("k1") is None
        assert cache.invalidate("nonexistent") is False

    def test_cache_clear(self):
        cache = KnowledgeCache(max_size=10, ttl_seconds=60, enabled=True)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        cache.clear()
        assert cache.get("k1") is None
        assert cache.stats["size"] == 0
        assert cache.stats["hits"] == 0

    def test_cache_evict_expired(self):
        cache = KnowledgeCache(max_size=10, ttl_seconds=0, enabled=True)
        cache.put("k1", "v1")
        cache.put("k2", "v2")
        time.sleep(0.05)
        evicted = cache._evict_expired()
        assert evicted == 2


# ---------------------------------------------------------
# 4. Postgres Metadata Tests (using SQLite in-memory)
# ---------------------------------------------------------
@pytest.fixture
def metadata_store():
    """Create an in-memory SQLite-backed metadata store for testing."""
    from app.analysis.knowledge.storage.postgres_metadata import (
        PostgresMetadataStore,
        KnowledgeDocumentRecord,
        KnowledgeChunkRecord,
    )
    from app.db.database import Base

    test_engine = create_engine("sqlite:///:memory:")
    # Create only the knowledge tables
    KnowledgeDocumentRecord.__table__.create(test_engine, checkfirst=True)
    KnowledgeChunkRecord.__table__.create(test_engine, checkfirst=True)

    TestSession = sessionmaker(bind=test_engine)
    store = PostgresMetadataStore(session_factory=TestSession)
    return store


class TestPostgresMetadataStore:
    def test_save_and_get_document(self, metadata_store):
        metadata_store.save_document(
            doc_id="doc_1", title="Test Doc",
            category="security", source="test.md",
            tags=["a", "b"], version="1.0", language="en",
            chunk_count=5, metadata={"key": "val"},
        )
        fetched = metadata_store.get_document("doc_1")
        assert fetched is not None
        assert fetched["title"] == "Test Doc"
        assert fetched["tags"] == ["a", "b"]

    def test_list_documents(self, metadata_store):
        metadata_store.save_document(
            doc_id="d1", title="Doc 1", category="security",
            source="a.md", tags=["x"], version="1.0",
            language="en", chunk_count=0, metadata={},
        )
        metadata_store.save_document(
            doc_id="d2", title="Doc 2", category="pattern",
            source="b.md", tags=["y"], version="1.0",
            language="en", chunk_count=0, metadata={},
        )
        docs = metadata_store.list_documents(category="security")
        assert len(docs) == 1
        assert docs[0]["document_id"] == "d1"

    def test_delete_document(self, metadata_store):
        metadata_store.save_document(
            doc_id="d1", title="Del", category="security",
            source="a.md", tags=[], version="1.0",
            language="en", chunk_count=0, metadata={},
        )
        assert metadata_store.delete_document("d1") is True
        assert metadata_store.get_document("d1") is None
        assert metadata_store.delete_document("nonexistent") is False

    def test_save_and_get_chunk(self, metadata_store):
        metadata_store.save_chunk_metadata(
            chunk_id="c1", document_id="doc1", chunk_index=0,
            category="security", tags=["test"],
            content_preview="Test content...", token_count=10,
            metadata={"header": "Section 1"},
        )
        chunk = metadata_store.get_chunk_metadata("c1")
        assert chunk is not None
        assert chunk["document_id"] == "doc1"
        assert chunk["token_count"] == 10

    def test_get_chunks_by_document(self, metadata_store):
        for i in range(3):
            metadata_store.save_chunk_metadata(
                chunk_id=f"c{i}", document_id="doc1", chunk_index=i,
                category="security", tags=[], content_preview=f"chunk {i}",
                token_count=5, metadata={},
            )
        chunks = metadata_store.get_chunks_by_document("doc1")
        assert len(chunks) == 3
        assert chunks[0]["chunk_index"] == 0
        assert chunks[2]["chunk_index"] == 2

    def test_delete_chunks_by_document(self, metadata_store):
        for i in range(3):
            metadata_store.save_chunk_metadata(
                chunk_id=f"c{i}", document_id="doc1", chunk_index=i,
                category="security", tags=[], content_preview="",
                token_count=0, metadata={},
            )
        deleted = metadata_store.delete_chunks_by_document("doc1")
        assert deleted == 3
        assert metadata_store.get_chunks_by_document("doc1") == []


# ---------------------------------------------------------
# 5. Providers Tests
# ---------------------------------------------------------
class TestProviders:
    def test_repository_provider(self, tmp_path):
        (tmp_path / "doc1.md").write_text("# Doc 1\nContent 1", encoding="utf-8")
        (tmp_path / "doc2.md").write_text("# Doc 2\nContent 2", encoding="utf-8")

        provider = RepositoryProvider(knowledge_dir=str(tmp_path))
        docs = provider.load_documents()

        assert len(docs) == 2
        assert provider.get_category() == DocumentCategory.REPOSITORY
        assert provider.provider_name == "RepositoryProvider"
        assert all(isinstance(d, KnowledgeDocument) for d in docs)
        titles = {d.title for d in docs}
        assert "Doc 1" in titles
        assert "Doc 2" in titles

    def test_security_provider_tags(self, tmp_path):
        (tmp_path / "owasp_top_10.md").write_text("# OWASP Top 10\nContent", encoding="utf-8")
        (tmp_path / "cwe_89.md").write_text("# CWE-89\nSQL Injection", encoding="utf-8")
        (tmp_path / "general_security.md").write_text("# General\nInfo", encoding="utf-8")

        provider = SecurityProvider(knowledge_dir=str(tmp_path))
        docs = provider.load_documents()

        assert len(docs) == 3
        owasp_docs = [d for d in docs if "owasp" in d.tags]
        cwe_docs = [d for d in docs if "cwe" in d.tags]
        assert len(owasp_docs) >= 1
        assert len(cwe_docs) >= 1

    def test_provider_missing_dir(self, tmp_path):
        provider = RepositoryProvider(knowledge_dir=str(tmp_path / "nonexistent"))
        docs = provider.load_documents()
        assert docs == []


# ---------------------------------------------------------
# 6. Repository Index Tests
# ---------------------------------------------------------
class TestRepositoryIndex:
    def test_repository_index_crud(self):
        index = RepositoryIndex()
        ctx = RepositoryContext(
            repository_url="https://github.com/user/repo",
            primary_language="python",
            framework="fastapi",
            dependencies=["pydantic"],
        )

        index.index_repository(ctx)
        fetched = index.get_context("https://github.com/user/repo")
        assert fetched is not None
        assert fetched.framework == "fastapi"

        index.update_cfg_summary("https://github.com/user/repo", {"nodes": 10})
        assert index.get_context("https://github.com/user/repo").cfg_summary == {"nodes": 10}

        repos = index.list_repositories()
        assert len(repos) == 1

        assert index.remove_repository("https://github.com/user/repo") is True
        assert index.get_context("https://github.com/user/repo") is None

    def test_get_dependencies_and_framework(self):
        index = RepositoryIndex()
        ctx = RepositoryContext(
            repository_url="https://github.com/user/repo2",
            framework="django",
            dependencies=["celery", "redis"],
        )
        index.index_repository(ctx)

        assert index.get_dependencies("https://github.com/user/repo2") == ["celery", "redis"]
        assert index.get_framework("https://github.com/user/repo2") == "django"

        # Non-existent repo
        assert index.get_dependencies("nonexistent") == []
        assert index.get_framework("nonexistent") == ""

    def test_update_summaries(self):
        index = RepositoryIndex()
        ctx = RepositoryContext(repository_url="http://repo")
        index.index_repository(ctx)

        index.update_call_graph_summary("http://repo", {"functions": 50})
        assert index.get_context("http://repo").call_graph_summary == {"functions": 50}

        index.update_data_flow_summary("http://repo", {"tainted": 3})
        assert index.get_context("http://repo").data_flow_summary == {"tainted": 3}


# ---------------------------------------------------------
# 7. Retriever & Reranker Tests
# ---------------------------------------------------------
class TestRetriever:
    def test_retriever_basic_flow(self):
        """Test retriever with proper mocked embedding provider and vector store."""
        chunk1 = _make_chunk(chunk_id="c1", content="SQL injection risk")
        chunk2 = _make_chunk(chunk_id="c2", content="XSS vulnerability")

        mock_embedding_provider = MagicMock(spec=EmbeddingProvider)
        mock_embedding_provider.embed_query.return_value = [0.1, 0.2, 0.3]

        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = [("c1", 0.95), ("c2", 0.85)]

        chunk_store = {"c1": chunk1, "c2": chunk2}
        cache = KnowledgeCache(max_size=10, ttl_seconds=60, enabled=False)

        retriever = SemanticRetriever(
            embedding_provider=mock_embedding_provider,
            vector_store=mock_vector_store,
            chunk_store=chunk_store,
            cache=cache,
        )

        req = RetrievalRequest(query="security", top_k=2, similarity_threshold=0.0)
        results = retriever.retrieve(req)

        assert len(results) == 2
        assert results[0].chunk.chunk_id == "c1"
        assert results[0].similarity_score == 0.95
        mock_embedding_provider.embed_query.assert_called_once_with("security")

    def test_retriever_filters_by_category(self):
        chunk1 = _make_chunk(chunk_id="c1", category=DocumentCategory.SECURITY)
        chunk2 = _make_chunk(chunk_id="c2", category=DocumentCategory.PATTERN)

        mock_embedding_provider = MagicMock(spec=EmbeddingProvider)
        mock_embedding_provider.embed_query.return_value = [0.1]

        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = [("c1", 0.9), ("c2", 0.8)]

        retriever = SemanticRetriever(
            embedding_provider=mock_embedding_provider,
            vector_store=mock_vector_store,
            chunk_store={"c1": chunk1, "c2": chunk2},
        )

        req = RetrievalRequest(
            query="test", top_k=10,
            categories=[DocumentCategory.SECURITY],
            similarity_threshold=0.0,
        )
        results = retriever.retrieve(req)

        assert len(results) == 1
        assert results[0].chunk.category == DocumentCategory.SECURITY

    def test_retriever_filters_by_threshold(self):
        chunk1 = _make_chunk(chunk_id="c1")

        mock_embedding_provider = MagicMock(spec=EmbeddingProvider)
        mock_embedding_provider.embed_query.return_value = [0.1]

        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = [("c1", 0.3)]

        retriever = SemanticRetriever(
            embedding_provider=mock_embedding_provider,
            vector_store=mock_vector_store,
            chunk_store={"c1": chunk1},
        )

        req = RetrievalRequest(query="test", top_k=10, similarity_threshold=0.5)
        results = retriever.retrieve(req)

        assert len(results) == 0

    def test_index_chunks(self):
        chunk = _make_chunk(chunk_id="c1")
        embedding = [0.1, 0.2, 0.3]

        mock_embedding_provider = MagicMock(spec=EmbeddingProvider)
        mock_vector_store = MagicMock()

        retriever = SemanticRetriever(
            embedding_provider=mock_embedding_provider,
            vector_store=mock_vector_store,
        )

        count = retriever.index_chunks([chunk], [embedding])
        assert count == 1
        assert "c1" in retriever._chunk_store
        mock_vector_store.add_embeddings.assert_called_once()

    def test_retriever_caching(self):
        chunk = _make_chunk(chunk_id="c1")

        mock_embedding_provider = MagicMock(spec=EmbeddingProvider)
        mock_embedding_provider.embed_query.return_value = [0.1]

        mock_vector_store = MagicMock()
        mock_vector_store.search.return_value = [("c1", 0.9)]

        cache = KnowledgeCache(max_size=10, ttl_seconds=60, enabled=True)

        retriever = SemanticRetriever(
            embedding_provider=mock_embedding_provider,
            vector_store=mock_vector_store,
            chunk_store={"c1": chunk},
            cache=cache,
        )

        req = RetrievalRequest(query="test", top_k=2, similarity_threshold=0.0)
        results1 = retriever.retrieve(req)
        results2 = retriever.retrieve(req)

        assert len(results1) == 1
        assert len(results2) == 1
        # embed_query should only be called once (second call is cached)
        assert mock_embedding_provider.embed_query.call_count == 1


class TestReranker:
    def test_reranker_scoring(self):
        reranker = WeightedReranker(
            similarity_weight=0.7,
            metadata_weight=0.1,
            category_weight=0.2,
            category_boosts={DocumentCategory.SECURITY: 0.1},
        )

        c1 = _make_chunk(chunk_id="c1", category=DocumentCategory.SECURITY, tags=["owasp"])
        c2 = _make_chunk(chunk_id="c2", category=DocumentCategory.BEST_PRACTICE)

        r1 = RetrievalResult(chunk=c1, similarity_score=0.8, final_score=0.8)
        r2 = RetrievalResult(chunk=c2, similarity_score=0.9, final_score=0.9)

        reranked = reranker.rerank([r1, r2], context=None)

        assert len(reranked) == 2
        assert all(r.final_score > 0 for r in reranked)

    def test_reranker_empty_results(self):
        reranker = WeightedReranker()
        reranked = reranker.rerank([], context=None)
        assert reranked == []

    def test_reranker_weight_warning(self):
        """Weights not summing to 1.0 should log a warning but not crash."""
        reranker = WeightedReranker(
            similarity_weight=0.5,
            metadata_weight=0.5,
            category_weight=0.5,
        )
        chunk = _make_chunk()
        r = RetrievalResult(chunk=chunk, similarity_score=0.8, final_score=0.8)
        reranked = reranker.rerank([r])
        assert len(reranked) == 1


# ---------------------------------------------------------
# 8. Query Engine Tests
# ---------------------------------------------------------
class TestQueryEngine:
    def test_query_engine_flow(self):
        chunk = _make_chunk()
        result = RetrievalResult(chunk=chunk, similarity_score=0.9, final_score=0.9)

        mock_retriever = MagicMock(spec=SemanticRetriever)
        mock_retriever.retrieve.return_value = [result]

        mock_reranker = MagicMock(spec=WeightedReranker)
        mock_reranker.rerank.side_effect = lambda results, context=None: results

        mock_repo_index = MagicMock(spec=RepositoryIndex)
        mock_repo_index.get_context.return_value = None

        engine = KnowledgeQueryEngine(
            retriever=mock_retriever,
            reranker=mock_reranker,
            repository_index=mock_repo_index,
        )

        res = engine.query(query="test", top_k=5, similarity_threshold=0.5)

        assert isinstance(res, RetrievedContext)
        assert res.query == "test"
        assert res.total_results == 1
        assert mock_retriever.retrieve.called
        assert mock_reranker.rerank.called

    def test_query_engine_with_repository_context(self):
        chunk = _make_chunk()
        result = RetrievalResult(chunk=chunk, similarity_score=0.9, final_score=0.9)

        mock_retriever = MagicMock(spec=SemanticRetriever)
        mock_retriever.retrieve.return_value = [result]

        mock_reranker = MagicMock(spec=WeightedReranker)
        mock_reranker.rerank.side_effect = lambda results, context=None: results

        repo_ctx = RepositoryContext(
            repository_url="https://github.com/test/repo",
            framework="fastapi",
        )
        repo_index = RepositoryIndex()
        repo_index.index_repository(repo_ctx)

        engine = KnowledgeQueryEngine(
            retriever=mock_retriever,
            reranker=mock_reranker,
            repository_index=repo_index,
        )

        res = engine.query(
            query="security", repository_url="https://github.com/test/repo",
        )
        assert isinstance(res, RetrievedContext)
        assert res.repository_context is not None
        assert res.repository_context.framework == "fastapi"

    def test_register_repository(self):
        mock_retriever = MagicMock(spec=SemanticRetriever)
        repo_index = RepositoryIndex()

        engine = KnowledgeQueryEngine(
            retriever=mock_retriever,
            repository_index=repo_index,
        )

        ctx = RepositoryContext(repository_url="http://repo")
        engine.register_repository(ctx)

        assert repo_index.get_context("http://repo") is not None


# ---------------------------------------------------------
# 9. Vector Store Tests (with real FAISS)
# ---------------------------------------------------------
class TestVectorStore:
    def test_add_and_search(self):
        from app.analysis.knowledge.storage.vector_store import FAISSVectorStore

        store = FAISSVectorStore(dimension=3)
        assert store.size == 0

        store.add_embeddings(
            chunk_ids=["c1", "c2"],
            embeddings=[[1.0, 0.0, 0.0], [0.0, 1.0, 0.0]],
        )
        assert store.size == 2

        results = store.search([1.0, 0.0, 0.0], top_k=2)
        assert len(results) == 2
        # First result should be c1 (exact match)
        assert results[0][0] == "c1"
        assert results[0][1] > 0.9

    def test_clear(self):
        from app.analysis.knowledge.storage.vector_store import FAISSVectorStore

        store = FAISSVectorStore(dimension=3)
        store.add_embeddings(["c1"], [[1.0, 0.0, 0.0]])
        assert store.size == 1

        store.clear()
        assert store.size == 0

    def test_empty_search(self):
        from app.analysis.knowledge.storage.vector_store import FAISSVectorStore

        store = FAISSVectorStore(dimension=3)
        results = store.search([1.0, 0.0, 0.0], top_k=5)
        assert results == []

    def test_mismatched_lengths(self):
        from app.analysis.knowledge.storage.vector_store import FAISSVectorStore

        store = FAISSVectorStore(dimension=3)
        with pytest.raises(ValueError):
            store.add_embeddings(["c1", "c2"], [[1.0, 0.0, 0.0]])

    def test_save_and_load(self, tmp_path):
        from app.analysis.knowledge.storage.vector_store import FAISSVectorStore

        path = str(tmp_path / "test.faiss")
        store = FAISSVectorStore(dimension=3, index_path=path)
        store.add_embeddings(["c1"], [[1.0, 0.0, 0.0]])
        store.save()

        store2 = FAISSVectorStore(dimension=3, index_path=path)
        store2.load()
        assert store2.size == 1
