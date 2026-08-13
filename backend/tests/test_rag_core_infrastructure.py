"""Tests for the RAG Core Infrastructure in app.analysis.RAG."""

import os
import tempfile
import pytest

from app.analysis.RAG.config.settings import RAGConfig, ChunkingConfig, EmbeddingConfig, VectorStoreConfig
from app.analysis.RAG.models.documents import (
    DocumentMetadata,
    KnowledgeDocument,
    KnowledgeChunk,
    EmbeddingDocument,
    SearchResult,
    ValidationResult,
    Severity,
    Priority,
)
from app.analysis.RAG.ingestion.discovery import discover_knowledge_files
from app.analysis.RAG.ingestion.parser import parse_frontmatter, extract_sections, parse_document
from app.analysis.RAG.ingestion.validator import validate_document, validate_batch
from app.analysis.RAG.ingestion.chunker import chunk_document, chunk_documents
from app.analysis.RAG.ingestion.pipeline import IndexingPipeline
from app.analysis.RAG.embeddings.mock_provider import MockEmbeddingProvider
from app.analysis.RAG.embeddings.service import EmbeddingService
from app.analysis.RAG.vector_store.memory_store import InMemoryVectorStore


class TestDocumentModels:
    """Test Pydantic v2 document models and frontmatter normalization."""

    def test_schema_a_frontmatter_normalization(self):
        """Test Schema A (Security docs format with 'id')."""
        fm = {
            "id": "OWASP-A01",
            "title": "Broken Access Control - Overview",
            "category": "security",
            "subcategory": "owasp",
            "language": ["python", "java"],
            "framework": ["fastapi", "spring_boot"],
            "severity": "critical",
            "priority": "high",
            "tags": ["access-control", "authorization"],
            "source": "OWASP Top 10 2021",
            "version": "2021",
        }
        meta = DocumentMetadata.from_frontmatter(fm)
        assert meta.document_id == "OWASP-A01"
        assert meta.title == "Broken Access Control - Overview"
        assert meta.category == "security"
        assert meta.subcategory == "owasp"
        assert meta.languages == ["python", "java"]
        assert meta.frameworks == ["fastapi", "spring_boot"]
        assert meta.severity == Severity.CRITICAL
        assert meta.priority == Priority.HIGH

    def test_schema_b_frontmatter_normalization(self):
        """Test Schema B (Python docs format with 'knowledge_id')."""
        fm = {
            "knowledge_id": "PYKB-COROUTINES",
            "title": "Coroutines and Awaitable Objects",
            "category": "python",
            "subcategory": "async",
            "languages": "python",
            "frameworks": ["fastapi"],
            "severity": "medium",
            "priority": "medium",
            "tags": ["python", "async"],
        }
        meta = DocumentMetadata.from_frontmatter(fm)
        assert meta.document_id == "PYKB-COROUTINES"
        assert meta.title == "Coroutines and Awaitable Objects"
        assert meta.category == "python"
        assert meta.languages == ["python"]
        assert meta.frameworks == ["fastapi"]
        assert meta.severity == Severity.MEDIUM

    def test_chunk_char_count(self):
        chunk = KnowledgeChunk(
            document_id="doc-1",
            content="Sample chunk content text",
        )
        assert chunk.char_count == len("Sample chunk content text")


class TestParserAndValidator:
    """Test frontmatter parsing, section extraction, and document validation."""

    def test_parse_frontmatter(self):
        raw = """---
id: TEST-01
title: Test Title
category: testing
---
# Section 1
Body content here.
"""
        fm, body = parse_frontmatter(raw)
        assert fm["id"] == "TEST-01"
        assert body.startswith("# Section 1")

    def test_extract_sections(self):
        body = """# Section One
Content 1

# Section Two
Content 2
"""
        sections = extract_sections(body)
        assert "Section One" in sections
        assert "Section Two" in sections
        assert sections["Section One"] == "Content 1"
        assert sections["Section Two"] == "Content 2"

    def test_validate_document(self):
        doc = KnowledgeDocument(
            metadata=DocumentMetadata(
                document_id="DOC-1",
                title="Valid Document Title",
                category="security",
                tags=["security", "test"],
            ),
            body="# Overview\nThis is a sufficiently long body content for the validation check to pass cleanly without issues.",
            sections={"Overview": "This is a sufficiently long body content for the validation check to pass cleanly without issues."},
            source_path="/fake/path.md",
        )
        res = validate_document(doc)
        assert res.is_valid
        assert res.metadata_present


class TestChunking:
    """Test semantic chunker."""

    def test_chunk_document_with_sections(self):
        doc = KnowledgeDocument(
            metadata=DocumentMetadata(
                document_id="DOC-CHUNK",
                title="Chunking Test",
                category="python",
                tags=["chunk"],
            ),
            body="# Overview\nParagraph 1.\n\nParagraph 2.\n\n# Details\nDetailed paragraph text.",
            sections={
                "Overview": "Paragraph 1.\n\nParagraph 2.",
                "Details": "Detailed paragraph text.",
            },
            source_path="/path/test.md",
        )
        config = ChunkingConfig(max_chunk_size=500, min_chunk_size=10, include_metadata_header=True)
        chunks = chunk_document(doc, config)
        assert len(chunks) == 2
        assert chunks[0].document_id == "DOC-CHUNK"
        assert chunks[0].section_title in ["Overview", "Details"]


class TestEmbeddingsAndVectorStore:
    """Test mock embedding provider, embedding service, and in-memory vector store."""

    def test_mock_embedding_provider(self):
        provider = MockEmbeddingProvider(dimension=768)
        emb1 = provider.embed_text("sample code text")
        emb2 = provider.embed_text("sample code text")
        assert len(emb1) == 768
        assert emb1 == emb2  # Deterministic

    def test_embedding_service_caching(self):
        provider = MockEmbeddingProvider(dimension=128)
        service = EmbeddingService(provider=provider, config=EmbeddingConfig(cache_enabled=True))
        emb1 = service.embed_text("caching test text")
        assert service.cache_size == 1
        emb2 = service.embed_text("caching test text")
        assert emb1 == emb2

    def test_in_memory_vector_store(self):
        store = InMemoryVectorStore()
        provider = MockEmbeddingProvider(dimension=64)
        emb = provider.embed_text("SQL injection vulnerability")

        doc = EmbeddingDocument(
            chunk_id="chunk-1",
            document_id="doc-1",
            content="SQL injection vulnerability content",
            embedding=emb,
            metadata={"category": "security", "tags": ["owasp", "sql-injection"]},
        )
        store.add_documents([doc])
        assert store.count() == 1

        query_emb = provider.embed_query("SQL injection")
        results = store.search(query_emb, top_k=5)
        assert len(results) == 1
        assert results[0].chunk_id == "chunk-1"
        assert results[0].score > 0.5


class TestIndexingPipeline:
    """Test full end-to-end indexing pipeline."""

    def test_pipeline_execution(self, tmp_path):
        # Create temp knowledge dir
        kdir = tmp_path / "knowledge"
        kdir.mkdir()
        subdir = kdir / "security"
        subdir.mkdir()
        md_file = subdir / "test_doc.md"
        md_file.write_text(
            """---
id: OWASP-TEST
title: OWASP Test Document
category: security
severity: high
priority: high
tags: [security, owasp]
---
# Overview
This is an overview of the security vulnerability test case.

# Why it matters
Security vulnerabilities compromise data integrity and system safety.
""",
            encoding="utf-8",
        )

        config = RAGConfig(knowledge_dir=str(kdir))
        embedder = MockEmbeddingProvider(dimension=128)
        store = InMemoryVectorStore()

        pipeline = IndexingPipeline(
            config=config,
            embedding_provider=embedder,
            vector_store=store,
        )

        stats = pipeline.run(force_reindex=True)
        assert stats.files_discovered == 1
        assert stats.files_parsed == 1
        assert stats.chunks_created > 0
        assert stats.vectors_stored > 0
        assert store.count() > 0
